from trytond.pool import Pool
from .purchase import *

def register():
    Pool.register(
        PurchaseLine,
        module='nodux_purchase', type_='model')
