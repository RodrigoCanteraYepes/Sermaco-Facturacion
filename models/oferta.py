# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class Oferta(models.Model):
    _name = 'oferta.oferta'
    _description = 'Gestión de Ofertas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'numero_oferta'

    # Campos básicos
    numero_oferta = fields.Char(
        string='Número de Oferta',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo')
    )
    
    name = fields.Char(
        string='Nombre de la Oferta',
        required=True,
        tracking=True
    )
    
    tipo_oferta = fields.Selection([
        ('proyectos', 'Proyectos'),
        ('venta_directa', 'Venta Directa')
    ], string='Tipo de Oferta', required=True, default='proyectos', tracking=True)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('enviada', 'Enviada'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada')
    ], string='Estado', default='borrador', tracking=True)
    
    # Relaciones
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )
    
    # Campo relacionado para compatibilidad con vistas
    cliente_id = fields.Many2one(
        'res.partner',
        related='partner_id',
        string='Cliente',
        store=True,
        readonly=False
    )
    
    lead_id = fields.Many2one(
        'crm.lead',
        string='Oportunidad',
        tracking=True
    )
    
    # Campo relacionado para compatibilidad con vistas
    oportunidad_id = fields.Many2one(
        'crm.lead',
        related='lead_id',
        string='Oportunidad',
        store=True,
        readonly=False
    )
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        readonly=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Técnico Comercial',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    # Campo relacionado para compatibilidad con vistas
    tecnico_comercial_id = fields.Many2one(
        'res.users',
        related='user_id',
        string='Técnico Comercial',
        store=True,
        readonly=False
    )
    
    # Fechas
    fecha_oferta = fields.Date(
        string='Fecha de Oferta',
        default=fields.Date.today,
        required=True
    )
    
    fecha_vencimiento = fields.Date(
        string='Fecha de Vencimiento',
        required=True
    )
    
    fecha_entrega_estimada = fields.Date(
        string='Fecha de Entrega Estimada'
    )
    
    # Campos monetarios
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    monto_total = fields.Monetary(
        string='Monto Total',
        currency_field='currency_id',
        compute='_compute_monto_total',
        store=True
    )
    
    margen_beneficio = fields.Float(
        string='Margen de Beneficio (%)',
        default=15.0
    )
    
    # Relaciones One2many
    capitulo_ids = fields.One2many(
        'oferta.capitulo',
        'oferta_id',
        string='Capítulos'
    )
    
    clausula_ids = fields.Many2many(
        'oferta.clausula',
        string='Cláusulas'
    )
    
    delegacion_ids = fields.One2many(
        'oferta.delegacion',
        'oferta_id',
        string='Delegaciones'
    )
    
    tarifa_ids = fields.One2many(
        'oferta.tarifa',
        'oferta_id',
        string='Tarifas'
    )
    
    # Campos de texto
    descripcion = fields.Html(
        string='Descripción'
    )
    
    observaciones = fields.Text(
        string='Observaciones'
    )
    
    condiciones_comerciales = fields.Html(
        string='Condiciones Comerciales'
    )
    
    # Campos computados
    tiene_capitulos = fields.Boolean(
        string='Tiene Capítulos',
        compute='_compute_tiene_capitulos'
    )
    
    capitulos_count = fields.Integer(
        string='Número de Capítulos',
        compute='_compute_capitulos_count'
    )
    
    clausulas_count = fields.Integer(
        string='Número de Cláusulas',
        compute='_compute_clausulas_count'
    )
    
    delegacion_obligatoria = fields.Boolean(
        string='Delegación Obligatoria',
        compute='_compute_delegacion_obligatoria'
    )
    
    integridad_completa = fields.Boolean(
        string='Integridad Completa',
        compute='_compute_integridad_completa'
    )
    
    # Campo relacionado para compatibilidad con vistas
    integridad_ok = fields.Boolean(
        related='integridad_completa',
        string='Integridad OK',
        store=True
    )
    
    # Campos de validación
    productos_sin_precio = fields.Boolean(
        string='Productos sin Precio',
        compute='_compute_productos_sin_precio'
    )
    
    capitulos_sin_productos = fields.Boolean(
        string='Capítulos sin Productos',
        compute='_compute_capitulos_sin_productos'
    )
    
    @api.model
    def create(self, vals):
        if vals.get('numero_oferta', _('Nuevo')) == _('Nuevo'):
            vals['numero_oferta'] = self.env['ir.sequence'].next_by_code('oferta.oferta') or _('Nuevo')
        return super(Oferta, self).create(vals)
    
    @api.depends('capitulo_ids', 'tarifa_ids')
    def _compute_monto_total(self):
        for record in self:
            total = 0.0
            if record.tipo_oferta == 'proyectos':
                for capitulo in record.capitulo_ids:
                    total += capitulo.subtotal
            else:
                for tarifa in record.tarifa_ids:
                    total += tarifa.precio_total
            record.monto_total = total
    
    @api.depends('capitulo_ids')
    def _compute_tiene_capitulos(self):
        for record in self:
            record.tiene_capitulos = bool(record.capitulo_ids)
    
    @api.depends('capitulo_ids')
    def _compute_capitulos_count(self):
        for record in self:
            record.capitulos_count = len(record.capitulo_ids)
    
    @api.depends('clausula_ids')
    def _compute_clausulas_count(self):
        for record in self:
            record.clausulas_count = len(record.clausula_ids)
    
    @api.depends('monto_total')
    def _compute_delegacion_obligatoria(self):
        limite_delegacion = float(self.env['ir.config_parameter'].sudo().get_param(
            'gestion_ofertas.limite_delegacion', '50000.0'
        ))
        for record in self:
            record.delegacion_obligatoria = record.monto_total > limite_delegacion
    
    @api.depends('capitulo_ids', 'clausula_ids', 'delegacion_ids', 'productos_sin_precio', 'capitulos_sin_productos')
    def _compute_integridad_completa(self):
        for record in self:
            integridad = True
            
            # Validar según tipo de oferta
            if record.tipo_oferta == 'proyectos':
                if not record.capitulo_ids:
                    integridad = False
                if record.capitulos_sin_productos:
                    integridad = False
            
            # Validar productos sin precio
            if record.productos_sin_precio:
                integridad = False
            
            # Validar delegación obligatoria
            if record.delegacion_obligatoria and not record.delegacion_ids:
                integridad = False
            
            # Validar cláusulas mínimas
            if len(record.clausula_ids) < 2:
                integridad = False
            
            record.integridad_completa = integridad
    
    @api.depends('capitulo_ids.producto_ids', 'tarifa_ids')
    def _compute_productos_sin_precio(self):
        for record in self:
            sin_precio = False
            
            if record.tipo_oferta == 'proyectos':
                for capitulo in record.capitulo_ids:
                    for producto in capitulo.producto_ids:
                        tarifa = record.tarifa_ids.filtered(
                            lambda t: t.producto_id.id == producto.id
                        )
                        if not tarifa or tarifa.precio <= 0:
                            sin_precio = True
                            break
                    if sin_precio:
                        break
            else:
                for tarifa in record.tarifa_ids:
                    if tarifa.precio <= 0:
                        sin_precio = True
                        break
            
            record.productos_sin_precio = sin_precio
    
    @api.depends('capitulo_ids.producto_ids')
    def _compute_capitulos_sin_productos(self):
        for record in self:
            sin_productos = False
            if record.tipo_oferta == 'proyectos':
                for capitulo in record.capitulo_ids:
                    if not capitulo.producto_ids:
                        sin_productos = True
                        break
            record.capitulos_sin_productos = sin_productos
    
    @api.onchange('tipo_oferta')
    def _onchange_tipo_oferta(self):
        if self.tipo_oferta == 'venta_directa' and self.capitulo_ids:
            return {
                'warning': {
                    'title': _('Advertencia'),
                    'message': _('Las ofertas de venta directa no utilizan capítulos. '
                               'Los capítulos existentes serán ignorados.')
                }
            }
    
    @api.onchange('fecha_oferta')
    def _onchange_fecha_oferta(self):
        if self.fecha_oferta:
            # Establecer fecha de vencimiento por defecto (30 días)
            self.fecha_vencimiento = self.fecha_oferta + timedelta(days=30)
    
    @api.constrains('fecha_vencimiento', 'fecha_oferta')
    def _check_fechas(self):
        for record in self:
            if record.fecha_vencimiento and record.fecha_oferta:
                if record.fecha_vencimiento <= record.fecha_oferta:
                    raise ValidationError(
                        _('La fecha de vencimiento debe ser posterior a la fecha de oferta.')
                    )
    
    @api.constrains('tipo_oferta', 'capitulo_ids')
    def _check_capitulos_venta_directa(self):
        for record in self:
            if record.tipo_oferta == 'venta_directa' and record.capitulo_ids:
                raise ValidationError(
                    _('Las ofertas de venta directa no pueden tener capítulos.')
                )
    
    def action_enviar_revision(self):
        """Envía la oferta a revisión"""
        self.ensure_one()
        if not self.integridad_completa:
            raise UserError(
                _('No se puede enviar a revisión una oferta con problemas de integridad. '
                  'Verifique que todos los campos obligatorios estén completos.')
            )
        self.state = 'en_revision'
        self.message_post(
            body=_('Oferta enviada a revisión por %s') % self.env.user.name
        )
    
    def action_aprobar(self):
        """Aprueba la oferta"""
        self.ensure_one()
        self.state = 'aprobada'
        self.message_post(
            body=_('Oferta aprobada por %s') % self.env.user.name
        )
    
    def action_enviar_cliente(self):
        """Envía la oferta al cliente"""
        self.ensure_one()
        if self.state != 'aprobada':
            raise UserError(_('Solo se pueden enviar ofertas aprobadas.'))
        self.state = 'enviada'
        self.message_post(
            body=_('Oferta enviada al cliente por %s') % self.env.user.name
        )
    
    def action_aceptar(self):
        """Marca la oferta como aceptada y crea orden de venta"""
        self.ensure_one()
        if self.state != 'enviada':
            raise UserError(_('Solo se pueden aceptar ofertas enviadas.'))
        
        # Crear orden de venta
        sale_order = self._crear_orden_venta()
        self.sale_order_id = sale_order.id
        self.state = 'aceptada'
        
        self.message_post(
            body=_('Oferta aceptada. Orden de venta creada: %s') % sale_order.name
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de Venta'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_rechazar(self):
        """Marca la oferta como rechazada"""
        self.ensure_one()
        self.state = 'rechazada'
        self.message_post(
            body=_('Oferta rechazada por el cliente')
        )
    
    def action_cancelar(self):
        """Cancela la oferta"""
        self.ensure_one()
        self.state = 'cancelada'
        self.message_post(
            body=_('Oferta cancelada por %s') % self.env.user.name
        )
    
    def action_reset_borrador(self):
        """Regresa la oferta a borrador"""
        self.ensure_one()
        self.state = 'borrador'
        self.message_post(
            body=_('Oferta regresada a borrador por %s') % self.env.user.name
        )
    
    def action_crear_pedido_venta(self):
        """Crea un pedido de venta basado en la oferta aceptada"""
        self.ensure_one()
        if self.state != 'aceptada':
            raise UserError(_('Solo se pueden crear pedidos de venta para ofertas aceptadas.'))
        
        # Crear orden de venta
        sale_order = self._crear_orden_venta()
        self.sale_order_id = sale_order.id
        
        self.message_post(
            body=_('Pedido de venta creado: %s') % sale_order.name
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pedido de Venta'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_sale_order(self):
        """Abre la vista del pedido de venta relacionado"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('Esta oferta no tiene un pedido de venta asociado.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pedido de Venta'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_opportunity(self):
        """Abre la vista de la oportunidad relacionada"""
        self.ensure_one()
        if not self.lead_id:
            raise UserError(_('Esta oferta no tiene una oportunidad asociada.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oportunidad'),
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _crear_orden_venta(self):
        """Crea una orden de venta basada en la oferta"""
        self.ensure_one()
        
        # Crear orden de venta
        sale_vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'date_order': fields.Datetime.now(),
            'validity_date': self.fecha_vencimiento,
            'note': self.observaciones,
            'opportunity_id': self.lead_id.id if self.lead_id else False,
        }
        
        sale_order = self.env['sale.order'].create(sale_vals)
        
        # Crear líneas de orden de venta
        if self.tipo_oferta == 'proyectos':
            for capitulo in self.capitulo_ids:
                for producto in capitulo.producto_ids:
                    tarifa = self.tarifa_ids.filtered(
                        lambda t: t.producto_id.id == producto.id
                    )
                    if tarifa:
                        line_vals = {
                            'order_id': sale_order.id,
                            'product_id': producto.id,
                            'product_uom_qty': tarifa.cantidad,
                            'price_unit': tarifa.precio,
                            'name': f'[{capitulo.nombre}] {producto.name}',
                        }
                        self.env['sale.order.line'].create(line_vals)
        else:
            for tarifa in self.tarifa_ids:
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': tarifa.producto_id.id,
                    'product_uom_qty': tarifa.cantidad,
                    'price_unit': tarifa.precio,
                }
                self.env['sale.order.line'].create(line_vals)
        
        return sale_order
    
    def action_generar_clausulas_automaticas(self):
        """Genera cláusulas automáticas según el tipo de cliente/proyecto"""
        self.ensure_one()
        
        # Buscar cláusulas generales activas
        clausulas_generales = self.env['oferta.clausula'].search([
            ('tipo', '=', 'general'),
            ('activa', '=', True)
        ])
        
        # Buscar cláusulas específicas según el sector del cliente
        clausulas_especificas = self.env['oferta.clausula'].search([
            ('tipo', '=', 'especifica'),
            ('activa', '=', True),
            '|',
            ('sector_ids', '=', False),
            ('sector_ids', 'in', [self.partner_id.industry_id.id] if self.partner_id.industry_id else [])
        ])
        
        # Asignar cláusulas
        self.clausula_ids = [(6, 0, (clausulas_generales + clausulas_especificas).ids)]
        
        self.message_post(
            body=_('Cláusulas automáticas generadas: %d generales, %d específicas') % 
                 (len(clausulas_generales), len(clausulas_especificas))
        )
    
    def action_generar_tarifas_automaticas(self):
        """Genera tarifas automáticas según productos en capítulos"""
        self.ensure_one()
        
        productos = self.env['product.product']
        
        if self.tipo_oferta == 'proyectos':
            for capitulo in self.capitulo_ids:
                productos |= capitulo.producto_ids
        
        for producto in productos:
            # Verificar si ya existe tarifa para este producto
            tarifa_existente = self.tarifa_ids.filtered(
                lambda t: t.producto_id.id == producto.id
            )
            
            if not tarifa_existente:
                # Crear nueva tarifa con precio base del producto
                tarifa_vals = {
                    'oferta_id': self.id,
                    'producto_id': producto.id,
                    'precio': producto.list_price,
                    'cantidad': 1.0,
                    'fecha_inicio': self.fecha_oferta,
                    'fecha_fin': self.fecha_vencimiento,
                }
                self.env['oferta.tarifa'].create(tarifa_vals)
        
        self.message_post(
            body=_('Tarifas automáticas generadas para %d productos') % len(productos)
        )