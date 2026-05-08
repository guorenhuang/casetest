"""
订单 / 订阅状态机：显式合法迁移；非法迁移抛 StateMachineError。

主文档：../state-machine.md
"""
from __future__ import annotations

from enum import Enum
from typing import FrozenSet


class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    active = "active"
    expired = "expired"
    refunded = "refunded"


class SubscriptionStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    refunded = "refunded"


class StateMachineError(ValueError):
    """非法状态迁移。"""

    def __init__(self, entity: str, current: str, target: str) -> None:
        super().__init__(f"{entity}: cannot transition {current!r} -> {target!r}")
        self.entity = entity
        self.current = current
        self.target = target


# 订单：pending → paid → active → expired | refunded
_ORDER_FROM: dict[OrderStatus, FrozenSet[OrderStatus]] = {
    OrderStatus.pending: frozenset({OrderStatus.paid, OrderStatus.refunded}),
    OrderStatus.paid: frozenset({OrderStatus.active, OrderStatus.refunded}),
    OrderStatus.active: frozenset({OrderStatus.expired, OrderStatus.refunded}),
    OrderStatus.expired: frozenset(),
    OrderStatus.refunded: frozenset(),
}

# 订阅：pending → active → expired | refunded
_SUB_FROM: dict[SubscriptionStatus, FrozenSet[SubscriptionStatus]] = {
    SubscriptionStatus.pending: frozenset({SubscriptionStatus.active, SubscriptionStatus.refunded}),
    SubscriptionStatus.active: frozenset({SubscriptionStatus.expired, SubscriptionStatus.refunded}),
    SubscriptionStatus.expired: frozenset(),
    SubscriptionStatus.refunded: frozenset(),
}


def transition_order(current: str | OrderStatus, target: str | OrderStatus) -> OrderStatus:
    cur_s = current if isinstance(current, str) else str(current.value)
    tgt_s = target if isinstance(target, str) else str(target.value)
    cur = OrderStatus(cur_s)
    tgt = OrderStatus(tgt_s)
    allowed = _ORDER_FROM.get(cur)
    if allowed is None or tgt not in allowed:
        raise StateMachineError("order", cur.value, tgt.value)
    return tgt


def transition_subscription(
    current: str | SubscriptionStatus, target: str | SubscriptionStatus
) -> SubscriptionStatus:
    cur_s = current if isinstance(current, str) else str(current.value)
    tgt_s = target if isinstance(target, str) else str(target.value)
    cur = SubscriptionStatus(cur_s)
    tgt = SubscriptionStatus(tgt_s)
    allowed = _SUB_FROM.get(cur)
    if allowed is None or tgt not in allowed:
        raise StateMachineError("subscription", cur.value, tgt.value)
    return tgt


def is_terminal_order(status: str | OrderStatus) -> bool:
    s = OrderStatus(str(status))
    return s in (OrderStatus.expired, OrderStatus.refunded)
