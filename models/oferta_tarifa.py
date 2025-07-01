# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class OfertaTarifa(models.Model):
    _name = 'oferta.tarifa'
    _description = 'Tarifas de Oferta'
    _order = 'oferta_id, producto_id, fecha_inicio'
    _rec_name = 'display_name'

    # Campos básicos
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True
    )
    
    # Relaciones
    oferta_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta',
        required=True,
        ondelete='cascade'
    )
    
    producto_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        domain=[('sale_ok', '=', True)]
    )
    
    # Campos de precio y cantidad
    precio = fields.Monetary(
        string='Precio Unitario',
        currency_field='currency_id',
        required=True
    )
    
    cantidad = fields.Float(
        string='Cantidad',
        default=1.0,
        required=True
    )
    
    precio_total = fields.Monetary(
        string='Precio Total',
        currency_field='currency_id',
        compute='_compute_precio_total',
        store=True
    )
    
    currency_id = fields.Many2one(
        related='oferta_id.currency_id',
        string='Moneda'
    )
    
    # Campos de fechas
    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        required=True,
        default=fields.Date.today
    )
    
    fecha_fin = fields.Date(
        string='Fecha de Fin',
        required=True
    )
    
    # Campos de descuento
    descuento_porcentaje = fields.Float(
        string='Descuento (%)',
        default=0.0
    )
    
    descuento_fijo = fields.Monetary(
        string='Descuento Fijo',
        currency_field='currency_id',
        default=0.0
    )
    
    precio_con_descuento = fields.Monetary(
        string='Precio con Descuento',
        currency_field='currency_id',
        compute='_compute_precio_con_descuento',
        store=True
    )
    
    total_con_descuento = fields.Monetary(
        string='Total con Descuento',
        currency_field='currency_id',
        compute='_compute_total_con_descuento',
        store=True
    )
    
    # Campos de configuración
    unidad_medida_id = fields.Many2one(
        related='producto_id.uom_id',
        string='Unidad de Medida'
    )
    
    tipo_tarifa = fields.Selection([
        ('estandar', 'Estándar'),
        ('promocional', 'Promocional'),
        ('especial', 'Especial'),
        ('volumen', 'Por Volumen')
    ], string='Tipo de Tarifa', default='estandar')
    
    activa = fields.Boolean(
        string='Activa',
        default=True
    )
    
    # Campos de información adicional
    observaciones = fields.Text(
        string='Observaciones'
    )
    
    condiciones_especiales = fields.Text(
        string='Condiciones Especiales'
    )
    
    # Campos de referencia
    precio_lista = fields.Monetary(
        string='Precio de Lista',
        related='producto_id.list_price',
        currency_field='currency_id',
        readonly=True
    )
    
    costo_producto = fields.Monetary(
        string='Costo del Producto',
        related='producto_id.standard_price',
        currency_field='currency_id',
        readonly=True
    )
    
    # Campos computados
    margen_unitario = fields.Monetary(
        string='Margen Unitario',
        currency_field='currency_id',
        compute='_compute_margen',
        store=True
    )
    
    margen_porcentaje = fields.Float(
        string='Margen (%)',
        compute='_compute_margen',
        store=True
    )
    
    margen_total = fields.Monetary(
        string='Margen Total',
        currency_field='currency_id',
        compute='_compute_margen',
        store=True
    )
    
    es_valida = fields.Boolean(
        string='Es Válida',
        compute='_compute_es_valida'
    )
    
    dias_vigencia = fields.Integer(
        string='Días de Vigencia',
        compute='_compute_dias_vigencia'
    )
    
    @api.depends('producto_id')
    def _compute_display_name(self):
        for record in self:
            if record.producto_id:
                record.display_name = f'{record.producto_id.name} - {record.precio} {record.currency_id.symbol if record.currency_id else ""}'
            else:
                record.display_name = _('Nueva Tarifa')
    
    @api.depends('precio', 'cantidad')
    def _compute_precio_total(self):
        for record in self:
            record.precio_total = record.precio * record.cantidad
    
    @api.depends('precio', 'descuento_porcentaje', 'descuento_fijo')
    def _compute_precio_con_descuento(self):
        for record in self:
            precio_descuento = record.precio
            
            # Aplicar descuento porcentual
            if record.descuento_porcentaje > 0:
                precio_descuento = precio_descuento * (1 - record.descuento_porcentaje / 100)
            
            # Aplicar descuento fijo
            if record.descuento_fijo > 0:
                precio_descuento = max(0, precio_descuento - record.descuento_fijo)
            
            record.precio_con_descuento = precio_descuento
    
    @api.depends('precio_con_descuento', 'cantidad')
    def _compute_total_con_descuento(self):
        for record in self:
            record.total_con_descuento = record.precio_con_descuento * record.cantidad
    
    @api.depends('precio_con_descuento', 'costo_producto', 'cantidad')
    def _compute_margen(self):
        for record in self:
            if record.costo_producto > 0:
                record.margen_unitario = record.precio_con_descuento - record.costo_producto
                record.margen_porcentaje = (record.margen_unitario / record.costo_producto) * 100
                record.margen_total = record.margen_unitario * record.cantidad
            else:
                record.margen_unitario = 0
                record.margen_porcentaje = 0
                record.margen_total = 0
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_es_valida(self):
        hoy = fields.Date.today()
        for record in self:
            record.es_valida = record.fecha_inicio <= hoy <= record.fecha_fin
    
    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_dias_vigencia(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin:
                delta = record.fecha_fin - record.fecha_inicio
                record.dias_vigencia = delta.days + 1
            else:
                record.dias_vigencia = 0
    
    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for record in self:
            if record.fecha_fin <= record.fecha_inicio:
                raise ValidationError(
                    _('La fecha de fin debe ser posterior a la fecha de inicio.')
                )
    
    @api.constrains('precio', 'cantidad')
    def _check_valores_positivos(self):
        for record in self:
            if record.precio < 0:
                raise ValidationError(_('El precio no puede ser negativo.'))
            if record.cantidad <= 0:
                raise ValidationError(_('La cantidad debe ser mayor a cero.'))
    
    @api.constrains('descuento_porcentaje')
    def _check_descuento_porcentaje(self):
        for record in self:
            if record.descuento_porcentaje < 0 or record.descuento_porcentaje > 100:
                raise ValidationError(
                    _('El descuento porcentual debe estar entre 0% y 100%.')
                )
    
    @api.constrains('producto_id', 'oferta_id', 'fecha_inicio', 'fecha_fin')
    def _check_tarifa_unica(self):
        for record in self:
            tarifas_solapadas = self.search([
                ('producto_id', '=', record.producto_id.id),
                ('oferta_id', '=', record.oferta_id.id),
                ('id', '!=', record.id),
                ('fecha_inicio', '<=', record.fecha_fin),
                ('fecha_fin', '>=', record.fecha_inicio)
            ])
            if tarifas_solapadas:
                raise ValidationError(
                    _('Ya existe una tarifa para el producto "%s" en el período especificado.') % 
                    record.producto_id.name
                )
    
    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        if self.producto_id:
            self.precio = self.producto_id.list_price
            if self.oferta_id:
                self.fecha_inicio = self.oferta_id.fecha_oferta
                self.fecha_fin = self.oferta_id.fecha_vencimiento
    
    @api.onchange('oferta_id')
    def _onchange_oferta_id(self):
        if self.oferta_id:
            self.fecha_inicio = self.oferta_id.fecha_oferta
            self.fecha_fin = self.oferta_id.fecha_vencimiento
    
    def action_aplicar_descuento_volumen(self):
        """Aplica descuento por volumen según la cantidad"""
        self.ensure_one()
        
        # Configurar descuentos por volumen
        descuentos_volumen = [
            (100, 5),   # 5% para cantidades >= 100
            (50, 3),    # 3% para cantidades >= 50
            (20, 1),    # 1% para cantidades >= 20
        ]
        
        descuento_aplicado = 0
        for cantidad_min, descuento in descuentos_volumen:
            if self.cantidad >= cantidad_min:
                descuento_aplicado = descuento
                break
        
        if descuento_aplicado > 0:
            self.descuento_porcentaje = descuento_aplicado
            self.tipo_tarifa = 'volumen'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Descuento Aplicado'),
                    'message': _('Se ha aplicado un descuento del %d%% por volumen.') % descuento_aplicado,
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin Descuento'),
                    'message': _('La cantidad no califica para descuento por volumen.'),
                    'type': 'info',
                }
            }
    
    def action_copiar_precio_lista(self):
        """Copia el precio de lista del producto"""
        self.ensure_one()
        if self.producto_id:
            self.precio = self.producto_id.list_price
            self.tipo_tarifa = 'estandar'
    
    def action_aplicar_margen_objetivo(self):
        """Aplica un margen objetivo sobre el costo"""
        self.ensure_one()
        if not self.costo_producto:
            raise ValidationError(
                _('No se puede calcular el margen porque el producto no tiene costo definido.')
            )
        
        margen_objetivo = self.oferta_id.margen_beneficio or 15.0
        precio_objetivo = self.costo_producto * (1 + margen_objetivo / 100)
        
        self.precio = precio_objetivo
        self.tipo_tarifa = 'especial'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Margen Aplicado'),
                'message': _('Se ha aplicado un margen del %.1f%% sobre el costo.') % margen_objetivo,
                'type': 'success',
            }
        }
    
    def action_extender_vigencia(self):
        """Extiende la vigencia de la tarifa"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extender Vigencia'),
            'res_model': 'oferta.tarifa.extender.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tarifa_id': self.id,
                'default_fecha_fin_actual': self.fecha_fin,
            }
        }
    
    @api.model
    def crear_tarifas_automaticas(self, oferta_id, productos):
        """Crea tarifas automáticas para una lista de productos"""
        oferta = self.env['oferta.oferta'].browse(oferta_id)
        tarifas_creadas = self.env['oferta.tarifa']
        
        for producto in productos:
            # Verificar si ya existe tarifa para este producto
            tarifa_existente = self.search([
                ('oferta_id', '=', oferta_id),
                ('producto_id', '=', producto.id)
            ])
            
            if not tarifa_existente:
                tarifa_vals = {
                    'oferta_id': oferta_id,
                    'producto_id': producto.id,
                    'precio': producto.list_price,
                    'cantidad': 1.0,
                    'fecha_inicio': oferta.fecha_oferta,
                    'fecha_fin': oferta.fecha_vencimiento,
                    'tipo_tarifa': 'estandar',
                }
                tarifa = self.create(tarifa_vals)
                tarifas_creadas |= tarifa
        
        return tarifas_creadas
    
    @api.model
    def get_precio_vigente(self, producto_id, fecha=None):
        """Obtiene el precio vigente para un producto en una fecha específica"""
        if not fecha:
            fecha = fields.Date.today()
        
        tarifa = self.search([
            ('producto_id', '=', producto_id),
            ('fecha_inicio', '<=', fecha),
            ('fecha_fin', '>=', fecha),
            ('activa', '=', True)
        ], limit=1)
        
        return tarifa.precio_con_descuento if tarifa else 0.0