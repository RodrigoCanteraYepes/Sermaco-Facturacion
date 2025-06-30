# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OfertaCapitulo(models.Model):
    _name = 'oferta.capitulo'
    _description = 'Capítulos de Oferta'
    _order = 'sequence, name'
    _rec_name = 'nombre'

    # Campos básicos
    nombre = fields.Char(
        string='Nombre del Capítulo',
        required=True
    )
    
    descripcion = fields.Text(
        string='Descripción'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    activo = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Relaciones
    oferta_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta',
        required=True,
        ondelete='cascade'
    )
    
    producto_ids = fields.Many2many(
        'product.product',
        'capitulo_producto_rel',
        'capitulo_id',
        'producto_id',
        string='Productos',
        domain=[('sale_ok', '=', True)]
    )
    
    clausula_ids = fields.Many2many(
        'oferta.clausula',
        'capitulo_clausula_rel',
        'capitulo_id',
        'clausula_id',
        string='Cláusulas Específicas'
    )
    
    # Campos de texto
    observaciones = fields.Text(
        string='Observaciones'
    )
    
    especificaciones_tecnicas = fields.Html(
        string='Especificaciones Técnicas'
    )
    
    # Campos computados
    productos_count = fields.Integer(
        string='Número de Productos',
        compute='_compute_productos_count'
    )
    
    clausulas_count = fields.Integer(
        string='Número de Cláusulas',
        compute='_compute_clausulas_count'
    )
    
    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True
    )
    
    currency_id = fields.Many2one(
        related='oferta_id.currency_id',
        string='Moneda'
    )
    
    tiene_productos = fields.Boolean(
        string='Tiene Productos',
        compute='_compute_tiene_productos'
    )
    
    productos_sin_precio = fields.Boolean(
        string='Productos sin Precio',
        compute='_compute_productos_sin_precio'
    )
    
    @api.depends('producto_ids')
    def _compute_productos_count(self):
        for record in self:
            record.productos_count = len(record.producto_ids)
    
    @api.depends('clausula_ids')
    def _compute_clausulas_count(self):
        for record in self:
            record.clausulas_count = len(record.clausula_ids)
    
    @api.depends('producto_ids', 'oferta_id.tarifa_ids')
    def _compute_subtotal(self):
        for record in self:
            total = 0.0
            for producto in record.producto_ids:
                tarifa = record.oferta_id.tarifa_ids.filtered(
                    lambda t: t.producto_id.id == producto.id
                )
                if tarifa:
                    total += tarifa[0].precio_total
            record.subtotal = total
    
    @api.depends('producto_ids')
    def _compute_tiene_productos(self):
        for record in self:
            record.tiene_productos = bool(record.producto_ids)
    
    @api.depends('producto_ids', 'oferta_id.tarifa_ids')
    def _compute_productos_sin_precio(self):
        for record in self:
            sin_precio = False
            for producto in record.producto_ids:
                tarifa = record.oferta_id.tarifa_ids.filtered(
                    lambda t: t.producto_id.id == producto.id
                )
                if not tarifa or tarifa.precio <= 0:
                    sin_precio = True
                    break
            record.productos_sin_precio = sin_precio
    
    @api.constrains('nombre')
    def _check_nombre_unico(self):
        for record in self:
            if record.oferta_id:
                capitulos_mismo_nombre = self.search([
                    ('oferta_id', '=', record.oferta_id.id),
                    ('nombre', '=', record.nombre),
                    ('id', '!=', record.id)
                ])
                if capitulos_mismo_nombre:
                    raise ValidationError(
                        _('Ya existe un capítulo con el nombre "%s" en esta oferta.') % record.nombre
                    )
    
    @api.onchange('producto_ids')
    def _onchange_producto_ids(self):
        """Crear tarifas automáticamente para productos nuevos"""
        if self.producto_ids and self.oferta_id:
            for producto in self.producto_ids:
                tarifa_existente = self.oferta_id.tarifa_ids.filtered(
                    lambda t: t.producto_id.id == producto.id
                )
                if not tarifa_existente:
                    # Crear nueva tarifa
                    tarifa_vals = {
                        'oferta_id': self.oferta_id.id,
                        'producto_id': producto.id,
                        'precio': producto.list_price,
                        'cantidad': 1.0,
                        'fecha_inicio': self.oferta_id.fecha_oferta,
                        'fecha_fin': self.oferta_id.fecha_vencimiento,
                    }
                    self.env['oferta.tarifa'].create(tarifa_vals)
    
    def action_agregar_productos_categoria(self):
        """Acción para agregar productos por categoría"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Agregar Productos por Categoría'),
            'res_model': 'oferta.capitulo.agregar.productos.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_capitulo_id': self.id,
                'default_oferta_id': self.oferta_id.id,
            }
        }
    
    def action_generar_clausulas_especificas(self):
        """Genera cláusulas específicas para este capítulo"""
        self.ensure_one()
        
        # Buscar cláusulas específicas relacionadas con los productos del capítulo
        categorias_productos = self.producto_ids.mapped('categ_id')
        
        clausulas_especificas = self.env['oferta.clausula'].search([
            ('tipo', '=', 'especifica'),
            ('activa', '=', True),
            '|',
            ('categoria_producto_ids', 'in', categorias_productos.ids),
            ('categoria_producto_ids', '=', False)
        ])
        
        # Agregar cláusulas al capítulo
        self.clausula_ids = [(6, 0, clausulas_especificas.ids)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cláusulas Generadas'),
                'message': _('Se han generado %d cláusulas específicas para este capítulo.') % len(clausulas_especificas),
                'type': 'success',
            }
        }
    
    def action_duplicar_capitulo(self):
        """Duplica el capítulo actual"""
        self.ensure_one()
        
        nuevo_capitulo = self.copy({
            'nombre': _('%s (Copia)') % self.nombre,
            'sequence': self.sequence + 1
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Capítulo Duplicado'),
            'res_model': 'oferta.capitulo',
            'res_id': nuevo_capitulo.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_ver_productos(self):
        """Acción para ver los productos del capítulo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Productos del Capítulo: %s') % self.nombre,
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.producto_ids.ids)],
            'context': {
                'search_default_sale_ok': 1,
            }
        }
    
    def action_ver_tarifas(self):
        """Acción para ver las tarifas de los productos del capítulo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tarifas del Capítulo: %s') % self.nombre,
            'res_model': 'oferta.tarifa',
            'view_mode': 'tree,form',
            'domain': [
                ('oferta_id', '=', self.oferta_id.id),
                ('producto_id', 'in', self.producto_ids.ids)
            ],
        }
    
    @api.model
    def create_from_template(self, template_id, oferta_id):
        """Crea un capítulo desde una plantilla"""
        template = self.browse(template_id)
        if not template.exists():
            return False
        
        nuevo_capitulo = template.copy({
            'oferta_id': oferta_id,
            'nombre': template.nombre,
        })
        
        return nuevo_capitulo