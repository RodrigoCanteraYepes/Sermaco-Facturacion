# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Campos relacionados con ofertas
    oferta_ids = fields.One2many(
        'oferta.oferta',
        'lead_id',
        string='Ofertas'
    )
    
    ofertas_count = fields.Integer(
        string='Número de Ofertas',
        compute='_compute_ofertas_count'
    )
    
    tiene_ofertas = fields.Boolean(
        string='Tiene Ofertas',
        compute='_compute_tiene_ofertas'
    )
    
    oferta_activa_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta Activa',
        compute='_compute_oferta_activa'
    )
    
    # Campos para automatización
    generar_oferta_automatica = fields.Boolean(
        string='Generar Oferta Automática',
        default=True,
        help='Si está marcado, se generará automáticamente una oferta cuando la oportunidad sea calificada'
    )
    
    tipo_oferta_preferido = fields.Selection([
        ('proyectos', 'Proyectos'),
        ('venta_directa', 'Venta Directa')
    ], string='Tipo de Oferta Preferido', default='proyectos')
    
    # Campos de requerimientos
    requerimientos_validados = fields.Boolean(
        string='Requerimientos Validados',
        default=False
    )
    
    requerimientos_detalle = fields.Html(
        string='Detalle de Requerimientos'
    )
    
    productos_requeridos_ids = fields.Many2many(
        'product.product',
        'lead_producto_requerido_rel',
        'lead_id',
        'producto_id',
        string='Productos Requeridos',
        domain=[('sale_ok', '=', True)]
    )
    
    # Campos de presupuesto
    presupuesto_estimado = fields.Monetary(
        string='Presupuesto Estimado',
        currency_field='company_currency'
    )
    
    presupuesto_confirmado = fields.Boolean(
        string='Presupuesto Confirmado',
        default=False
    )
    
    # Campos de tiempo
    fecha_entrega_requerida = fields.Date(
        string='Fecha de Entrega Requerida'
    )
    
    urgencia = fields.Selection([
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('critica', 'Crítica')
    ], string='Urgencia', default='normal')
    
    @api.depends('oferta_ids')
    def _compute_ofertas_count(self):
        for record in self:
            record.ofertas_count = len(record.oferta_ids)
    
    @api.depends('oferta_ids')
    def _compute_tiene_ofertas(self):
        for record in self:
            record.tiene_ofertas = bool(record.oferta_ids)
    
    @api.depends('oferta_ids')
    def _compute_oferta_activa(self):
        for record in self:
            oferta_activa = record.oferta_ids.filtered(
                lambda o: o.state in ['borrador', 'en_revision', 'aprobada', 'enviada']
            )
            record.oferta_activa_id = oferta_activa[0] if oferta_activa else False
    
    def action_ver_ofertas(self):
        """Acción para ver las ofertas de la oportunidad"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ofertas de %s') % self.name,
            'res_model': 'oferta.oferta',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_tipo_oferta': self.tipo_oferta_preferido,
            }
        }
    
    def action_crear_oferta(self):
        """Acción para crear una nueva oferta"""
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(
                _('Debe tener un cliente asignado antes de crear una oferta.')
            )
        
        if not self.requerimientos_validados:
            raise UserError(
                _('Los requerimientos deben estar validados antes de crear una oferta.')
            )
        
        # Crear oferta
        oferta_vals = self._preparar_valores_oferta()
        oferta = self.env['oferta.oferta'].create(oferta_vals)
        
        # Crear capítulos y productos si es necesario
        if self.tipo_oferta_preferido == 'proyectos' and self.productos_requeridos_ids:
            self._crear_capitulos_automaticos(oferta)
        
        # Crear tarifas automáticas
        if self.productos_requeridos_ids:
            self.env['oferta.tarifa'].crear_tarifas_automaticas(
                oferta.id, 
                self.productos_requeridos_ids
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva Oferta'),
            'res_model': 'oferta.oferta',
            'res_id': oferta.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _preparar_valores_oferta(self):
        """Prepara los valores para crear una oferta"""
        self.ensure_one()
        
        # Calcular fecha de vencimiento (30 días por defecto)
        fecha_vencimiento = fields.Date.today()
        if self.fecha_entrega_requerida:
            fecha_vencimiento = min(
                self.fecha_entrega_requerida,
                fields.Date.today() + fields.timedelta(days=30)
            )
        else:
            fecha_vencimiento = fields.Date.today() + fields.timedelta(days=30)
        
        return {
            'name': f'Oferta para {self.name}',
            'lead_id': self.id,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id or self.env.user.id,
            'tipo_oferta': self.tipo_oferta_preferido,
            'fecha_oferta': fields.Date.today(),
            'fecha_vencimiento': fecha_vencimiento,
            'fecha_entrega_estimada': self.fecha_entrega_requerida,
            'descripcion': self.requerimientos_detalle,
            'observaciones': f'Oferta generada automáticamente desde oportunidad: {self.name}',
        }
    
    def _crear_capitulos_automaticos(self, oferta):
        """Crea capítulos automáticos basados en categorías de productos"""
        self.ensure_one()
        
        # Agrupar productos por categoría
        categorias_productos = {}
        for producto in self.productos_requeridos_ids:
            categoria = producto.categ_id
            if categoria not in categorias_productos:
                categorias_productos[categoria] = []
            categorias_productos[categoria].append(producto)
        
        # Crear capítulos por categoría
        for categoria, productos in categorias_productos.items():
            capitulo_vals = {
                'oferta_id': oferta.id,
                'nombre': categoria.name,
                'descripcion': f'Capítulo generado automáticamente para productos de la categoría {categoria.name}',
                'producto_ids': [(6, 0, [p.id for p in productos])]
            }
            self.env['oferta.capitulo'].create(capitulo_vals)
    
    def action_validar_requerimientos(self):
        """Acción para validar requerimientos"""
        self.ensure_one()
        
        if not self.requerimientos_detalle:
            raise UserError(
                _('Debe especificar el detalle de requerimientos antes de validar.')
            )
        
        self.requerimientos_validados = True
        self.message_post(
            body=_('Requerimientos validados por %s') % self.env.user.name
        )
        
        # Si está configurado para generar oferta automática, crearla
        if self.generar_oferta_automatica and not self.oferta_ids:
            return self.action_crear_oferta()
    
    def action_invalidar_requerimientos(self):
        """Acción para invalidar requerimientos"""
        self.ensure_one()
        self.requerimientos_validados = False
        self.message_post(
            body=_('Requerimientos invalidados por %s') % self.env.user.name
        )
    
    def action_configurar_productos_requeridos(self):
        """Abre wizard para configurar productos requeridos"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Configurar Productos Requeridos'),
            'res_model': 'crm.lead.productos.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_productos_actuales': [(6, 0, self.productos_requeridos_ids.ids)]
            }
        }
    
    def action_crear_oferta_manual(self):
        """Crea una oferta manual sin validaciones automáticas"""
        self.ensure_one()
        
        # Crear oferta básica
        oferta_vals = {
            'name': f'Oferta Manual - {self.name}',
            'partner_id': self.partner_id.id,
            'lead_id': self.id,
            'user_id': self.user_id.id or self.env.user.id,
            'fecha_oferta': fields.Date.today(),
            'tipo_oferta': 'venta_directa',
            'observaciones': f'Oferta creada manualmente desde oportunidad: {self.name}',
        }
        
        oferta = self.env['oferta.oferta'].create(oferta_vals)
        
        self.message_post(
            body=_('Oferta manual creada: %s') % oferta.name
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oferta Manual'),
            'res_model': 'oferta.oferta',
            'res_id': oferta.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """Override create para configuraciones automáticas"""
        lead = super(CrmLead, self).create(vals)
        
        # Configurar tipo de oferta preferido según el sector del cliente
        if lead.partner_id and lead.partner_id.industry_id:
            # Sectores que típicamente usan proyectos
            sectores_proyectos = self.env['res.partner.industry'].search([
                ('name', 'ilike', 'construcción'),
                ('name', 'ilike', 'ingeniería'),
                ('name', 'ilike', 'consultoría'),
            ])
            
            if lead.partner_id.industry_id in sectores_proyectos:
                lead.tipo_oferta_preferido = 'proyectos'
            else:
                lead.tipo_oferta_preferido = 'venta_directa'
        
        return lead
    
    def write(self, vals):
        """Override write para automatizaciones"""
        result = super(CrmLead, self).write(vals)
        
        # Si se marca como ganada y tiene oferta activa, actualizar la oferta
        if vals.get('stage_id'):
            stage = self.env['crm.stage'].browse(vals['stage_id'])
            if stage.is_won:
                for lead in self:
                    if lead.oferta_activa_id and lead.oferta_activa_id.state == 'enviada':
                        lead.oferta_activa_id.action_aceptar()
        
        return result
    
    def _crear_oferta_automatica(self):
        """Método para crear oferta automática cuando se califique la oportunidad"""
        for lead in self:
            if (lead.generar_oferta_automatica and 
                lead.requerimientos_validados and 
                lead.partner_id and 
                not lead.oferta_ids):
                
                lead.action_crear_oferta()