# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OfertaClausula(models.Model):
    _name = 'oferta.clausula'
    _description = 'Cláusulas de Oferta'
    _order = 'tipo, sequence, nombre'
    _rec_name = 'nombre'

    # Campos básicos
    nombre = fields.Char(
        string='Nombre de la Cláusula',
        required=True
    )
    
    codigo = fields.Char(
        string='Código',
        help='Código único para identificar la cláusula'
    )
    
    tipo = fields.Selection([
        ('general', 'General'),
        ('especifica', 'Específica')
    ], string='Tipo de Cláusula', required=True, default='general')
    
    contenido = fields.Html(
        string='Contenido de la Cláusula',
        required=True,
        translate=True
    )
    
    descripcion = fields.Text(
        string='Descripción',
        translate=True
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    activa = fields.Boolean(
        string='Activa',
        default=True
    )
    
    obligatoria = fields.Boolean(
        string='Obligatoria',
        default=False,
        help='Si está marcada, esta cláusula se incluirá automáticamente en todas las ofertas'
    )
    
    # Campos de aplicabilidad
    aplicable_proyectos = fields.Boolean(
        string='Aplicable a Proyectos',
        default=True
    )
    
    aplicable_venta_directa = fields.Boolean(
        string='Aplicable a Venta Directa',
        default=True
    )
    
    # Relaciones
    sector_ids = fields.Many2many(
        'res.partner.industry',
        'clausula_sector_rel',
        'clausula_id',
        'sector_id',
        string='Sectores Aplicables',
        help='Si se especifican sectores, la cláusula solo se aplicará a clientes de estos sectores'
    )
    
    categoria_producto_ids = fields.Many2many(
        'product.category',
        'clausula_categoria_rel',
        'clausula_id',
        'categoria_id',
        string='Categorías de Producto',
        help='Categorías de productos a las que aplica esta cláusula'
    )
    
    pais_ids = fields.Many2many(
        'res.country',
        'clausula_pais_rel',
        'clausula_id',
        'pais_id',
        string='Países Aplicables'
    )
    
    # Campos de validez
    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        help='Fecha desde la cual la cláusula es válida'
    )
    
    fecha_fin = fields.Date(
        string='Fecha de Fin',
        help='Fecha hasta la cual la cláusula es válida'
    )
    
    # Campos monetarios para cláusulas con condiciones económicas
    monto_minimo = fields.Monetary(
        string='Monto Mínimo',
        currency_field='currency_id',
        help='Monto mínimo de la oferta para que aplique esta cláusula'
    )
    
    monto_maximo = fields.Monetary(
        string='Monto Máximo',
        currency_field='currency_id',
        help='Monto máximo de la oferta para que aplique esta cláusula'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    # Campos de configuración
    requiere_aprobacion = fields.Boolean(
        string='Requiere Aprobación',
        default=False,
        help='Si está marcada, las ofertas con esta cláusula requerirán aprobación adicional'
    )
    
    nivel_aprobacion = fields.Selection([
        ('supervisor', 'Supervisor'),
        ('gerente', 'Gerente'),
        ('director', 'Director')
    ], string='Nivel de Aprobación')
    
    # Campos de auditoría
    user_id = fields.Many2one(
        'res.users',
        string='Creado por',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    fecha_creacion = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now,
        readonly=True
    )
    
    # Campos computados
    ofertas_count = fields.Integer(
        string='Número de Ofertas',
        compute='_compute_ofertas_count'
    )
    
    es_valida = fields.Boolean(
        string='Es Válida',
        compute='_compute_es_valida'
    )
    
    # Relación inversa con ofertas
    oferta_ids = fields.Many2many(
        'oferta.oferta',
        'oferta_oferta_clausula_rel',
        'clausula_id',
        'oferta_id',
        string='Ofertas Relacionadas',
        compute='_compute_oferta_ids',
        store=False
    )
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_es_valida(self):
        hoy = fields.Date.today()
        for record in self:
            valida = True
            if record.fecha_inicio and record.fecha_inicio > hoy:
                valida = False
            if record.fecha_fin and record.fecha_fin < hoy:
                valida = False
            record.es_valida = valida
    
    def _compute_ofertas_count(self):
        for record in self:
            count = self.env['oferta.oferta'].search_count([
                ('clausula_ids', 'in', record.id)
            ])
            record.ofertas_count = count
    
    def _compute_oferta_ids(self):
        for record in self:
            ofertas = self.env['oferta.oferta'].search([
                ('clausula_ids', 'in', record.id)
            ])
            record.oferta_ids = ofertas
    
    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas_validez(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                if record.fecha_fin <= record.fecha_inicio:
                    raise ValidationError(
                        _('La fecha de fin debe ser posterior a la fecha de inicio.')
                    )
    
    @api.constrains('monto_minimo', 'monto_maximo')
    def _check_montos(self):
        for record in self:
            if record.monto_minimo and record.monto_maximo:
                if record.monto_maximo <= record.monto_minimo:
                    raise ValidationError(
                        _('El monto máximo debe ser mayor al monto mínimo.')
                    )
    
    @api.constrains('codigo')
    def _check_codigo_unico(self):
        for record in self:
            if record.codigo:
                clausulas_mismo_codigo = self.search([
                    ('codigo', '=', record.codigo),
                    ('id', '!=', record.id)
                ])
                if clausulas_mismo_codigo:
                    raise ValidationError(
                        _('Ya existe una cláusula con el código "%s".') % record.codigo
                    )
    
    def action_ver_ofertas(self):
        """Acción para ver las ofertas que usan esta cláusula"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ofertas con Cláusula: %s') % self.nombre,
            'res_model': 'oferta.oferta',
            'view_mode': 'tree,form',
            'domain': [('clausula_ids', 'in', self.id)],
        }
    
    def action_duplicar_clausula(self):
        """Duplica la cláusula actual"""
        self.ensure_one()
        
        nueva_clausula = self.copy({
            'nombre': _('%s (Copia)') % self.nombre,
            'codigo': False,  # El código debe ser único
            'activa': False,  # La copia inicia inactiva
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cláusula Duplicada'),
            'res_model': 'oferta.clausula',
            'res_id': nueva_clausula.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_activar_desactivar(self):
        """Activa o desactiva la cláusula"""
        for record in self:
            record.activa = not record.activa
        
        mensaje = _('Cláusulas activadas') if self[0].activa else _('Cláusulas desactivadas')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Estado Actualizado'),
                'message': mensaje,
                'type': 'success',
            }
        }
    
    def action_activar(self):
        """Activa la cláusula"""
        self.ensure_one()
        self.activa = True
        estado = 'activada'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Estado Actualizado'),
                'message': _('Cláusula %s') % estado,
                'type': 'success',
            }
        }
    
    def action_desactivar(self):
        """Desactiva la cláusula"""
        self.ensure_one()
        self.activa = False
        estado = 'desactivada'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Estado Actualizado'),
                'message': _('Cláusula %s') % estado,
                'type': 'success',
            }
        }
    
    @api.model
    def get_clausulas_aplicables(self, oferta):
        """Obtiene las cláusulas aplicables para una oferta específica"""
        domain = [
            ('activa', '=', True),
            ('es_valida', '=', True)
        ]
        
        # Filtrar por tipo de oferta
        if oferta.tipo_oferta == 'proyectos':
            domain.append(('aplicable_proyectos', '=', True))
        else:
            domain.append(('aplicable_venta_directa', '=', True))
        
        # Filtrar por sector del cliente
        if oferta.partner_id.industry_id:
            domain = ['|'] + domain + [
                ('sector_ids', '=', False),
                ('sector_ids', 'in', oferta.partner_id.industry_id.id)
            ]
        
        # Filtrar por país del cliente
        if oferta.partner_id.country_id:
            domain = ['|'] + domain + [
                ('pais_ids', '=', False),
                ('pais_ids', 'in', oferta.partner_id.country_id.id)
            ]
        
        # Filtrar por monto
        if oferta.monto_total:
            domain.extend([
                '|', ('monto_minimo', '=', False), ('monto_minimo', '<=', oferta.monto_total),
                '|', ('monto_maximo', '=', False), ('monto_maximo', '>=', oferta.monto_total)
            ])
        
        return self.search(domain)
    
    @api.model
    def get_clausulas_obligatorias(self, tipo_oferta):
        """Obtiene las cláusulas obligatorias para un tipo de oferta"""
        domain = [
            ('activa', '=', True),
            ('obligatoria', '=', True),
            ('es_valida', '=', True)
        ]
        
        if tipo_oferta == 'proyectos':
            domain.append(('aplicable_proyectos', '=', True))
        else:
            domain.append(('aplicable_venta_directa', '=', True))
        
        return self.search(domain)
    
    def preview_clausula(self):
        """Vista previa del contenido de la cláusula"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vista Previa: %s') % self.nombre,
            'res_model': 'oferta.clausula.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_clausula_id': self.id,
            }
        }