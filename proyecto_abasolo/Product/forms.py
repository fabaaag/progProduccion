from django import forms
from django.core.exceptions import ObjectDoesNotExist
from .models import Producto, FamiliaProducto, SubfamiliaProducto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        codigo_producto = cleaned_data.get('codigo_producto')

        codigo_familia = codigo_producto[:2]

        try:
            product_family = FamiliaProducto.objects.get(codigo_familia=codigo_familia)
        except ObjectDoesNotExist:
            self.add_error('product_family', 'No ProductFamily found for codigo_familia {}'.format(codigo_familia))
            product_family = None

        cleaned_data['product_family'] = product_family

        codigo_subfamilia = codigo_producto[:5]

        try:
            product_subfamily = SubfamiliaProducto.objects.get(codigo_subfamilia=codigo_subfamilia, product_family=product_family)
        except ObjectDoesNotExist:
            self.add_error('product_subfamily', 'No ProductSubfamily found for codigo_subfamilia{}'.format(codigo_subfamilia))
            product_subfamily = None

        cleaned_data['product_subfamily'] = product_subfamily

        return cleaned_data