"""simple test, just for development, not productionised"""

from main import BouquetDesign, Flower, FlowerBank

design1 = BouquetDesign.parse('AS1a2b1k8')
design2 = BouquetDesign.parse('AL2d3r7')
print(design1)
print(design2)
assert 'AS1a2b1k8' == str(design1)
assert 'AL2d3r7' == str(design2)

flowers_store = FlowerBank()

flowers = ['aS', 'aS', 'bL', 'bL', 'tS', 'tL', 'tM', 'aS']
for flower_str in flowers:
    flowers_store.add_flower(Flower(flower_str[0], flower_str[1]))
print(flowers_store.bank)
assert 3 == flowers_store.bank.get('aS').count

flowers_store.request_bouquet(design1)
flowers_store.request_bouquet(design2)

assert 3 == flowers_store.bank.get('rL').needed

print('-' * 50)
print(flowers_store.bank)

assert {'a': 2} == flowers_store.take_extra_flowers(2, 'S')
assert {'a': 2, 't': 1} == flowers_store.take_extra_flowers(3, 'S')
