import sys
from dataclasses import dataclass, field
from typing import Dict, List
from collections import defaultdict
import re


@dataclass()
class Bouquet:
    name: str
    size: str
    flowers: Dict[str, int]

    def add_flowers(self, flowers: Dict[str, int]):
        for flower, count in flowers.items():
            self.flowers[flower] += count

    def __str__(self):
        return (
                f"{self.name}{self.size}" +
                "".join(str(count) + name for name, count
                        in self.flowers.items())
        )


@dataclass()
class BouquetDesign(Bouquet):
    total_quantity: int
    extra_flowers_count: int = 0
    # I know this is wrong design to place queue_number here, but I hurry up :)
    queue_number = int = 0

    @classmethod
    def parse(cls, line):
        name = line[0]
        size = line[1]
        total = int(re.findall('[A-z]([0-9]+)$', line)[0])
        flowers = defaultdict(
            int,
            {i[2]: int(i[1]) for i in re.findall('(([0-9]+)([a-z]))', line)}
        )
        total_flowers_quantity = sum(flowers.values())
        return cls(
            name=name, size=size, flowers=flowers, total_quantity=total,
            extra_flowers_count=total - total_flowers_quantity
        )

    def __hash__(self):
        return self.queue_number

    def __str__(self):
        return (
                f"{self.name}{self.size}" +
                "".join(str(count) + name for name, count
                        in self.flowers.items()) +
                f"{self.total_quantity}"
        )


@dataclass
class Flower:
    name: str
    size: str

    @property
    def key(self):
        return self.name + self.size


@dataclass
class FlowerBankItem:
    flower: Flower
    count: int
    needed: int
    bouquet_queue: List[BouquetDesign] = field(default_factory=list)


class FlowerBank(dict):
    def __init__(self):
        super().__init__()
        self.total_by_size = defaultdict(int)
        self.total_needed_by_size = defaultdict(int)
        self.bank = {}
        # dict[bouquet_size, count],
        # how many flowers of specific size and any type needed
        self.need_any = defaultdict(int)
        # bouquet designs that need some extra flowers
        self.need_any_queue = defaultdict(int)

    def add_flower(self, flower: Flower):
        item = self.bank.get(flower.key)
        if not item:
            item = FlowerBankItem(flower, count=1, needed=0)
            self.bank[flower.key] = item
        else:
            self.bank[flower.key].count += 1

        self.total_by_size[flower.size] += 1
        self.total_needed_by_size[flower.size] += 1

    def request_bouquet(self, bouquet_design: BouquetDesign):
        self.total_needed_by_size[bouquet_design.size] += (
            bouquet_design.total_quantity)

        for flower, count in bouquet_design.flowers.items():
            key = flower + bouquet_design.size
            item = self.bank.get(key)
            if not item:
                self.bank[key] = FlowerBankItem(
                    flower=Flower(flower, bouquet_design.size),
                    count=0, needed=count, bouquet_queue=[bouquet_design]
                )
            else:
                item.needed += count
                item.bouquet_queue.append(bouquet_design)

        extra_count = (
                bouquet_design.total_quantity
                - sum(bouquet_design.flowers.values())
        )
        if extra_count > 0:
            self.need_any[bouquet_design.size] += extra_count
            self.need_any_queue[bouquet_design] = extra_count

    def clean_bouquet_queue(self, bouquet_design):
        if bouquet_design in self.need_any_queue:
            del self.need_any_queue[bouquet_design]
        for flower in bouquet_design.flowers.keys():
            if (
                    bouquet_design in
                    self.bank[flower + bouquet_design.size].bouquet_queue
            ):
                (self.bank[flower + bouquet_design.size]
                 .bouquet_queue.remove(bouquet_design))

    def take_extra_flowers(self, count, size) -> Dict[str, int]:
        """
        this method should select extra flowers smartly,
        but I have no time, let it be at least not stupid
        """
        total_taken = 0
        index = 0
        flowers = defaultdict(int)
        sorted_by_need = sorted(
            [[i.flower.name, i.count, i.count - i.needed]
             for i in self.bank.values()
             if i.flower.size == size], key=lambda x: x[2], reverse=True)

        stage = 1
        while total_taken < count:
            to_take_from = sorted_by_need[index]
            if to_take_from[2] > 0:
                total_taken += to_take_from[2]
                to_take_from[1] -= to_take_from[2]
                flowers[to_take_from[0]] += to_take_from[2]
                to_take_from[2] = 0
            elif to_take_from[1] > 0 and stage > 1:
                allow_to_take = min(to_take_from[1] // 5 + 1,
                                    count - total_taken)
                total_taken += allow_to_take
                to_take_from[1] -= allow_to_take
                flowers[to_take_from[0]] += allow_to_take
            index += 1
            if index > len(sorted_by_need) - 1:
                index = 0
                stage += 1

        return flowers

    def _try_to_make_bouquet(self, design: BouquetDesign):
        for flower, count in design.flowers.items():
            if self.bank[flower + design.size].count < count:
                return

        if design.total_quantity > self.total_by_size[design.size]:
            return
        if design.extra_flowers_count > self.need_any[design.size]:
            return

        bouquet = Bouquet(design.name, design.size, defaultdict(int))

        extra_flowers = self.take_extra_flowers(
            design.extra_flowers_count, design.size
        )
        bouquet.add_flowers(design.flowers)
        bouquet.add_flowers(extra_flowers)

        for flower, count in bouquet.flowers.items():
            self.bank[flower + design.size].count -= count
            self.bank[flower + design.size].needed -= count

        self.total_by_size[bouquet.size] -= design.total_quantity

        self.need_any[bouquet.size] -= sum(extra_flowers.values())

        return bouquet

    def try_to_make_bouquet(
            self, bouquet_designs_list: List[BouquetDesign]
    ) -> any([Bouquet, None]):
        for bouquet_design in bouquet_designs_list:
            bouquet = self._try_to_make_bouquet(bouquet_design)
            if bouquet:
                self.clean_bouquet_queue(bouquet_design)
                return bouquet

    def __getitem__(self, item):
        return self.bank[item]


def run(stream):
    flowers_store = FlowerBank()

    queue_counter = 0
    for input_line in stream:
        input_line = input_line.strip()
        if not input_line:
            continue
        if input_line[0].islower():
            flower = Flower(input_line[0], input_line[1])
            flowers_store.add_flower(flower)

            bouquet_queue = flowers_store[flower.key].bouquet_queue
            need_any_queue = [
                design for design, count in flowers_store.need_any_queue.items()
                if count <= flowers_store.total_by_size[design.size]
            ]
            # merge is better, but in fact unless len ~ 1000000 sorted is better
            merged_queue = sorted(need_any_queue + bouquet_queue,
                                  key=lambda i: i.queue_number)
            new_bouquet = flowers_store.try_to_make_bouquet(merged_queue)
            if new_bouquet:
                print(new_bouquet)
        else:
            next_design = BouquetDesign.parse(input_line)
            next_design.queue_number = queue_counter
            queue_counter += 1
            flowers_store.request_bouquet(next_design)

            new_bouquet = flowers_store.try_to_make_bouquet([next_design])
            if new_bouquet:
                print(new_bouquet)


if __name__ == '__main__':
    run(sys.stdin)
