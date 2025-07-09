# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos relacionados con ofertas
    oferta_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta Origen',
        readonly=True,
        help='Oferta desde la cual se generó esta orden de venta'
    )
    
    tiene_oferta_origen = fields.Boolean(
        string='Tiene Oferta Origen',
        compute='_compute_tiene_oferta_origen'
    )
    
    # Campos de información de la oferta
    numero_oferta = fields.Char(
        string='Número de Oferta',
        related='oferta_id.numero_oferta',
        readonly=True
    )
    
    tipo_oferta_origen = fields.Selection(
        related='oferta_id.tipo_oferta',
        string='Tipo de Oferta Origen',
        readonly=True
    )
    
    fecha_oferta_origen = fields.Date(
        string='Fecha de Oferta',
        related='oferta_id.fecha_oferta',
        readonly=True
    )
    
    # Campos de delegación y aprobación
    delegaciones_oferta_ids = fields.One2many(
        related='oferta_id.delegacion_ids',
        string='Delegaciones de la Oferta',
        readonly=True
    )
    
    clausulas_oferta_ids = fields.Many2many(
        related='oferta_id.clausula_ids',
        string='Cláusulas de la Oferta',
        readonly=True
    )
    
    # Campos de seguimiento
    margen_oferta = fields.Float(
        string='Margen de la Oferta (%)',
        related='oferta_id.margen_beneficio',
        readonly=True
    )
    
    @api.depends('oferta_id')
    def _compute_tiene_oferta_origen(self):
        for record in self:
            record.tiene_oferta_origen = bool(record.oferta_id)
    
    def action_ver_oferta_origen(self):
        """Acción para ver la oferta origen"""
        self.ensure_one()
        if not self.oferta_id:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oferta Origen'),
            'res_model': 'oferta.oferta',
            'res_id': self.oferta_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_ver_delegaciones_oferta(self):
        """Acción para ver las delegaciones de la oferta"""
        self.ensure_one()
        if not self.oferta_id:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delegaciones de la Oferta'),
            'res_model': 'oferta.delegacion',
            'view_mode': 'list,form',
            'domain': [('oferta_id', '=', self.oferta_id.id)],
        }
    
    def action_ver_clausulas_oferta(self):
        """Acción para ver las cláusulas de la oferta"""
        self.ensure_one()
        if not self.oferta_id:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cláusulas de la Oferta'),
            'res_model': 'oferta.clausula',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.clausulas_oferta_ids.ids)],
        }
    
    @api.model
    def create(self, vals):
        """Override create para configuraciones automáticas desde oferta"""
        sale_order = super(SaleOrder, self).create(vals)
        
        # Si se crea desde una oferta, aplicar configuraciones adicionales
        if sale_order.oferta_id:
            sale_order._aplicar_configuraciones_oferta()
        
        return sale_order
    
    def _aplicar_configuraciones_oferta(self):
        """Aplica configuraciones específicas de la oferta"""
        self.ensure_one()
        
        if not self.oferta_id:
            return
        
        # Aplicar condiciones comerciales de la oferta
        if self.oferta_id.condiciones_comerciales:
            self.note = self.oferta_id.condiciones_comerciales
        
        # Configurar términos de pago según el tipo de oferta
        if self.oferta_id.tipo_oferta == 'proyectos':
            # Para proyectos, buscar términos de pago específicos
            terminos_proyecto = self.env['account.payment.term'].search([
                ('name', 'ilike', 'proyecto')
            ], limit=1)
            if terminos_proyecto:
                self.payment_term_id = terminos_proyecto.id
        
        # Configurar fecha de entrega
        if self.oferta_id.fecha_entrega_estimada:
            self.commitment_date = self.oferta_id.fecha_entrega_estimada
        
        # Aplicar descuentos globales si existen
        self._aplicar_descuentos_oferta()
    
    def _aplicar_descuentos_oferta(self):
        """Aplica descuentos específicos de la oferta"""
        self.ensure_one()
        
        if not self.oferta_id:
            return
        
        # Buscar tarifas con descuentos en la oferta
        tarifas_con_descuento = self.oferta_id.tarifa_ids.filtered(
            lambda t: t.descuento_porcentaje > 0 or t.descuento_fijo > 0
        )
        
        for tarifa in tarifas_con_descuento:
            # Buscar la línea correspondiente en la orden de venta
            linea = self.order_line.filtered(
                lambda l: l.product_id.id == tarifa.producto_id.id
            )
            
            if linea:
                # Aplicar descuento
                if tarifa.descuento_porcentaje > 0:
                    linea.discount = tarifa.descuento_porcentaje
                elif tarifa.descuento_fijo > 0:
                    # Para descuento fijo, calcular el porcentaje equivalente
                    if linea.price_unit > 0:
                        descuento_porcentaje = (tarifa.descuento_fijo / linea.price_unit) * 100
                        linea.discount = min(descuento_porcentaje, 100)
    
    def action_generar_reporte_comparativo(self):
        """Genera un reporte comparativo entre la oferta y la orden de venta"""
        self.ensure_one()
        
        if not self.oferta_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin Oferta Origen'),
                    'message': _('Esta orden de venta no tiene una oferta origen.'),
                    'type': 'warning',
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reporte Comparativo Oferta vs Orden'),
            'res_model': 'sale.order.comparativo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_oferta_id': self.oferta_id.id,
            }
        }
    
    def action_sincronizar_con_oferta(self):
        """Sincroniza cambios con la oferta origen"""
        self.ensure_one()
        
        if not self.oferta_id:
            return
        
        # Actualizar fechas en la oferta
        if self.commitment_date:
            self.oferta_id.fecha_entrega_estimada = self.commitment_date
        
        # Actualizar observaciones
        if self.note and self.note != self.oferta_id.observaciones:
            self.oferta_id.observaciones = f"{self.oferta_id.observaciones or ''}\n\nActualización desde orden de venta:\n{self.note}"
        
        self.oferta_id.message_post(
            body=_('Información sincronizada desde la orden de venta %s') % self.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sincronización Completada'),
                'message': _('La información se ha sincronizado con la oferta origen.'),
                'type': 'success',
            }
        }
    
    def write(self, vals):
        """Override write para sincronización automática"""
        result = super(SaleOrder, self).write(vals)
        
        # Campos que deben sincronizarse automáticamente con la oferta
        campos_sincronizar = ['commitment_date', 'note']
        
        if any(campo in vals for campo in campos_sincronizar):
            for order in self:
                if order.oferta_id:
                    # Sincronizar automáticamente ciertos cambios
                    if 'commitment_date' in vals and vals['commitment_date']:
                        order.oferta_id.fecha_entrega_estimada = vals['commitment_date']
        
        return result