# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductSelectorWizard(models.TransientModel):
    _name = 'product.selector.wizard'
    _description = 'Asistente para Selección de Productos por Categoría'
    
    categoria_id = fields.Many2one(
        'product.categoria',
        string='Categoría',
        required=True,
        help='Selecciona la categoría de productos'
    )
    
    search_term = fields.Char(
        string='Buscar Producto',
        help='Introduce el nombre o código del producto a buscar'
    )
    
    product_ids = fields.Many2many(
        'product.template',
        string='Productos Disponibles',
        compute='_compute_product_ids',
        help='Productos filtrados por categoría y término de búsqueda'
    )
    
    selected_product_ids = fields.Many2many(
        'product.template',
        'wizard_product_rel',
        'wizard_id',
        'product_id',
        string='Productos Seleccionados'
    )
    
    oferta_id = fields.Many2one(
        'oferta.oferta',
        string='Oferta',
        help='Oferta a la que se agregarán los productos'
    )
    
    @api.depends('categoria_id', 'search_term')
    def _compute_product_ids(self):
        for wizard in self:
            domain = [('active', '=', True)]
            
            if wizard.categoria_id:
                domain.append(('categoria_oferta_id', '=', wizard.categoria_id.id))
            
            if wizard.search_term:
                search_domain = [
                    '|', '|', '|',
                    ('name', 'ilike', wizard.search_term),
                    ('default_code', 'ilike', wizard.search_term),
                    ('tags_busqueda', 'ilike', wizard.search_term),
                    ('description', 'ilike', wizard.search_term)
                ]
                domain = ['&'] + domain + search_domain
            
            wizard.product_ids = self.env['product.template'].search(domain)
    
    def action_add_products_to_oferta(self):
        """Agregar productos seleccionados a la oferta"""
        if not self.selected_product_ids:
            raise UserError(_('Debe seleccionar al menos un producto.'))
        
        if not self.oferta_id:
            raise UserError(_('Debe especificar una oferta.'))
        
        # Crear tarifas para cada producto seleccionado
        for product in self.selected_product_ids:
            # Verificar si el producto ya existe en la oferta
            existing_tarifa = self.env['oferta.tarifa'].search([
                ('oferta_id', '=', self.oferta_id.id),
                ('producto_id', '=', product.product_variant_id.id)
            ], limit=1)
            
            if not existing_tarifa:
                # Determinar el precio según el tipo de producto
                precio = product.list_price
                if product.es_alquiler and product.precio_alquiler_diario:
                    precio = product.precio_alquiler_diario
                elif product.es_porte and product.precio_porte_km:
                    precio = product.precio_porte_km
                
                self.env['oferta.tarifa'].create({
                    'oferta_id': self.oferta_id.id,
                    'producto_id': product.product_variant_id.id,
                    'precio': precio,
                    'cantidad': 1.0,
                    'fecha_inicio': fields.Date.today(),
                    'fecha_fin': self.oferta_id.fecha_vencimiento or fields.Date.today(),
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oferta'),
            'res_model': 'oferta.oferta',
            'res_id': self.oferta_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_products_by_category(self):
        """Ver productos filtrados por categoría"""
        if not self.categoria_id:
            raise UserError(_('Debe seleccionar una categoría.'))
        
        domain = [('categoria_oferta_id', '=', self.categoria_id.id)]
        
        if self.search_term:
            search_domain = [
                '|', '|', '|',
                ('name', 'ilike', self.search_term),
                ('default_code', 'ilike', self.search_term),
                ('tags_busqueda', 'ilike', self.search_term),
                ('description', 'ilike', self.search_term)
            ]
            domain = ['&'] + domain + search_domain
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Productos - %s') % self.categoria_id.name,
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': domain,
            'context': {
                'search_default_categoria_oferta_id': self.categoria_id.id,
                'default_categoria_oferta_id': self.categoria_id.id,
            },
            'target': 'current',
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def action_add_to_oferta_wizard(self):
        """Abrir wizard para agregar producto a oferta"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Agregar a Oferta'),
            'res_model': 'product.selector.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_selected_product_ids': [(6, 0, [self.id])],
                'default_categoria_id': self.categoria_oferta_id.id if self.categoria_oferta_id else False,
            }
        }