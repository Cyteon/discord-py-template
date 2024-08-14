# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

from __future__ import annotations

from dataclasses import dataclass

from typing import Final

def guild_data_template(guild_id):
    return {
        "id": guild_id,
        "daily_cash": 50,
        "log_channel": 0,
    }

def user_data_template(user_id, guild_id):
    return {
        "id": user_id,
        "guild_id": guild_id,
        "wallet": 0,
        "last_daily": 0,
        "last_robbed_at": 0,
        "jailed": False,
        "warnings": [],
    }

def user_global_data_template(user_id):
    return {
        "id": user_id,
        "blacklisted": False,
        "blacklist_reason": "",
    }
