#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
from decimal import Decimal
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond import backend
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['PurchaseLine']
__metaclass__ = PoolMeta

class PurchaseLine():
    'Purchase'
    __name__ = 'purchase.line'

    @fields.depends('product', 'unit', 'quantity', 'description',
        '_parent_purchase.party', '_parent_purchase.currency',
        '_parent_purchase.purchase_date')
    def on_change_product(self):
        Product = Pool().get('product.product')

        if not self.product:
            return {}
        res = {}

        context = {}
        party = None
        if self.purchase and self.purchase.party:
            party = self.purchase.party
            if party.lang:
                context['language'] = party.lang.code

        category = self.product.purchase_uom.category
        if not self.unit or self.unit not in category.uoms:
            res['unit'] = self.product.purchase_uom.id
            self.unit = self.product.purchase_uom
            res['unit.rec_name'] = self.product.purchase_uom.rec_name
            res['unit_digits'] = self.product.purchase_uom.digits

        with Transaction().set_context(self._get_context_purchase_price()):
            res['unit_price'] = Product.get_purchase_price([self.product],
                abs(self.quantity or 0))[self.product.id]
            if res['unit_price']:
                res['unit_price'] = res['unit_price'].quantize(
                    Decimal(1) / 10 ** self.__class__.unit_price.digits[1])
        res['taxes'] = []
        pattern = self._get_tax_rule_pattern()
        for tax in self.product.supplier_taxes_used:
            if party and party.supplier_tax_rule:
                tax_ids = party.supplier_tax_rule.apply(tax, pattern)
                if tax_ids:
                    res['taxes'].extend(tax_ids)
                continue
            res['taxes'].append(tax.id)
        if party and party.supplier_tax_rule:
            tax_ids = party.supplier_tax_rule.apply(None, pattern)
            if tax_ids:
                res['taxes'].extend(tax_ids)

        with Transaction().set_context(context):
            res['description'] = Product(self.product.id).rec_name

        self.unit_price = res['unit_price']
        self.type = 'line'
        res['amount'] = self.on_change_with_amount()
        return res
