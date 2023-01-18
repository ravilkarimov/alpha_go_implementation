from typing import List, Optional, Self

import attr


@attr.s(auto_attribs=True)
class Node:
    val: int
    children: Optional[List[Self]]
