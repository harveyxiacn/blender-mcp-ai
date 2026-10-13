"""
Preset animation handler

Handles preset animation, action library, NLA and related commands.
"""

from typing import Any

import bpy

# Preset animation configuration - enhanced version with more game animations
ANIMATION_PRESETS = {
    # ==================== Basic Actions ====================
    "idle": {
        "description": "Idle breathing",
        "category": "basic",
        "duration": 60,
        "loop": True,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (30, [0.02, 0, 0]), (60, [0, 0, 0])],
            "spine.001": [(1, [0, 0, 0]), (30, [0.01, 0, 0]), (60, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (45, [0.02, 0, 0]), (60, [0, 0, 0])],
        },
    },
    "idle_combat": {
        "description": "Combat idle",
        "category": "combat",
        "duration": 40,
        "loop": True,
        "keyframes": {
            "spine": [(1, [0.1, 0, 0]), (20, [0.12, 0, 0]), (40, [0.1, 0, 0])],
            "upper_arm.R": [(1, [0.3, 0, -0.5]), (40, [0.3, 0, -0.5])],
            "upper_arm.L": [(1, [0.2, 0, 0.3]), (40, [0.2, 0, 0.3])],
            "thigh.L": [(1, [0.1, 0, 0]), (40, [0.1, 0, 0])],
            "thigh.R": [(1, [-0.1, 0, 0]), (40, [-0.1, 0, 0])],
        },
    },
    "walk": {
        "description": "Walk cycle",
        "category": "locomotion",
        "duration": 24,
        "loop": True,
        "keyframes": {
            "thigh.L": [(1, [0.3, 0, 0]), (12, [-0.3, 0, 0]), (24, [0.3, 0, 0])],
            "thigh.R": [(1, [-0.3, 0, 0]), (12, [0.3, 0, 0]), (24, [-0.3, 0, 0])],
            "shin.L": [(1, [0.2, 0, 0]), (12, [0.5, 0, 0]), (24, [0.2, 0, 0])],
            "shin.R": [(1, [0.5, 0, 0]), (12, [0.2, 0, 0]), (24, [0.5, 0, 0])],
            "upper_arm.L": [(1, [-0.2, 0, 0]), (12, [0.2, 0, 0]), (24, [-0.2, 0, 0])],
            "upper_arm.R": [(1, [0.2, 0, 0]), (12, [-0.2, 0, 0]), (24, [0.2, 0, 0])],
        },
    },
    "run": {
        "description": "Run cycle",
        "category": "locomotion",
        "duration": 16,
        "loop": True,
        "keyframes": {
            "thigh.L": [(1, [0.5, 0, 0]), (8, [-0.5, 0, 0]), (16, [0.5, 0, 0])],
            "thigh.R": [(1, [-0.5, 0, 0]), (8, [0.5, 0, 0]), (16, [-0.5, 0, 0])],
            "shin.L": [(1, [0.3, 0, 0]), (8, [0.8, 0, 0]), (16, [0.3, 0, 0])],
            "shin.R": [(1, [0.8, 0, 0]), (8, [0.3, 0, 0]), (16, [0.8, 0, 0])],
            "upper_arm.L": [(1, [-0.4, 0, 0]), (8, [0.4, 0, 0]), (16, [-0.4, 0, 0])],
            "upper_arm.R": [(1, [0.4, 0, 0]), (8, [-0.4, 0, 0]), (16, [0.4, 0, 0])],
            "spine": [(1, [0.1, 0, 0]), (8, [-0.05, 0, 0]), (16, [0.1, 0, 0])],
        },
    },
    "sprint": {
        "description": "Sprint",
        "category": "locomotion",
        "duration": 12,
        "loop": True,
        "keyframes": {
            "thigh.L": [(1, [0.7, 0, 0]), (6, [-0.7, 0, 0]), (12, [0.7, 0, 0])],
            "thigh.R": [(1, [-0.7, 0, 0]), (6, [0.7, 0, 0]), (12, [-0.7, 0, 0])],
            "shin.L": [(1, [0.4, 0, 0]), (6, [1.0, 0, 0]), (12, [0.4, 0, 0])],
            "shin.R": [(1, [1.0, 0, 0]), (6, [0.4, 0, 0]), (12, [1.0, 0, 0])],
            "upper_arm.L": [(1, [-0.6, 0, 0]), (6, [0.6, 0, 0]), (12, [-0.6, 0, 0])],
            "upper_arm.R": [(1, [0.6, 0, 0]), (6, [-0.6, 0, 0]), (12, [0.6, 0, 0])],
            "spine": [(1, [0.2, 0, 0]), (6, [0.1, 0, 0]), (12, [0.2, 0, 0])],
        },
    },
    "jump": {
        "description": "Jump",
        "category": "locomotion",
        "duration": 40,
        "loop": False,
        "keyframes": {
            "root": [
                (1, [0, 0, 0]),
                (10, [0, 0, -0.1]),
                (20, [0, 0, 0.5]),
                (30, [0, 0, 0.5]),
                (40, [0, 0, 0]),
            ],
            "thigh.L": [(1, [0, 0, 0]), (10, [0.5, 0, 0]), (20, [-0.2, 0, 0]), (40, [0, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (10, [0.5, 0, 0]), (20, [-0.2, 0, 0]), (40, [0, 0, 0])],
            "upper_arm.L": [(1, [0, 0, 0]), (10, [0, 0, -0.5]), (20, [0, 0, 0.8]), (40, [0, 0, 0])],
            "upper_arm.R": [(1, [0, 0, 0]), (10, [0, 0, 0.5]), (20, [0, 0, -0.8]), (40, [0, 0, 0])],
        },
    },
    "double_jump": {
        "description": "Double jump",
        "category": "locomotion",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "root": [(1, [0, 0, 0.3]), (10, [0, 0, 0.6]), (20, [0, 0, 0.8]), (30, [0, 0, 0.4])],
            "thigh.L": [(1, [-0.2, 0, 0]), (15, [0.3, 0, 0]), (30, [-0.1, 0, 0])],
            "thigh.R": [(1, [-0.2, 0, 0]), (15, [0.3, 0, 0]), (30, [-0.1, 0, 0])],
            "spine": [(1, [-0.1, 0, 0]), (15, [0.1, 0, 0]), (30, [0, 0, 0])],
        },
    },
    "land": {
        "description": "Land",
        "category": "locomotion",
        "duration": 20,
        "loop": False,
        "keyframes": {
            "thigh.L": [(1, [-0.1, 0, 0]), (8, [0.5, 0, 0]), (20, [0, 0, 0])],
            "thigh.R": [(1, [-0.1, 0, 0]), (8, [0.5, 0, 0]), (20, [0, 0, 0])],
            "shin.L": [(1, [0.2, 0, 0]), (8, [0.8, 0, 0]), (20, [0, 0, 0])],
            "shin.R": [(1, [0.2, 0, 0]), (8, [0.8, 0, 0]), (20, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (8, [0.15, 0, 0]), (20, [0, 0, 0])],
        },
    },
    "dodge_roll": {
        "description": "Dodge roll",
        "category": "combat",
        "duration": 24,
        "loop": False,
        "keyframes": {
            "spine": [
                (1, [0, 0, 0]),
                (6, [1.0, 0, 0]),
                (12, [2.0, 0, 0]),
                (18, [3.0, 0, 0]),
                (24, [0, 0, 0]),
            ],
            "thigh.L": [(1, [0, 0, 0]), (12, [1.2, 0, 0]), (24, [0, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (12, [1.2, 0, 0]), (24, [0, 0, 0])],
            "upper_arm.L": [(1, [0, 0, 0]), (12, [0.5, 0, 0.5]), (24, [0, 0, 0])],
            "upper_arm.R": [(1, [0, 0, 0]), (12, [0.5, 0, -0.5]), (24, [0, 0, 0])],
        },
    },
    "dodge_back": {
        "description": "Back dodge",
        "category": "combat",
        "duration": 20,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (5, [-0.2, 0, 0]), (10, [-0.1, 0, 0]), (20, [0, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (10, [0.4, 0, 0]), (20, [0, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (10, [0.4, 0, 0]), (20, [0, 0, 0])],
        },
    },
    # ==================== Combat Actions ====================
    "attack": {
        "description": "Basic attack",
        "category": "combat",
        "duration": 20,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (5, [0, 0.8, -0.5]),
                (10, [0.5, -0.5, 0]),
                (20, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (5, [0.5, 0, 0]), (10, [0, 0, 0]), (20, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (5, [0, 0.2, 0]), (10, [0, -0.3, 0]), (20, [0, 0, 0])],
        },
    },
    "attack_combo_1": {
        "description": "Combo hit 1",
        "category": "combat",
        "duration": 15,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (5, [0.3, 0.5, -0.3]),
                (10, [0.5, -0.3, 0.2]),
                (15, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (5, [0.4, 0, 0]), (15, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (5, [0, 0.15, 0]), (10, [0, -0.2, 0]), (15, [0, 0, 0])],
        },
    },
    "attack_combo_2": {
        "description": "Combo hit 2",
        "category": "combat",
        "duration": 18,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [
                (1, [0, 0, 0]),
                (6, [0.3, -0.5, 0.3]),
                (12, [0.5, 0.3, -0.2]),
                (18, [0, 0, 0]),
            ],
            "forearm.L": [(1, [0, 0, 0]), (6, [0.4, 0, 0]), (18, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (6, [0, -0.15, 0]), (12, [0, 0.2, 0]), (18, [0, 0, 0])],
        },
    },
    "attack_combo_3": {
        "description": "Combo hit 3 (heavy)",
        "category": "combat",
        "duration": 25,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (8, [-0.3, 1.0, -0.8]),
                (15, [0.8, -0.8, 0.3]),
                (25, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (8, [0.6, 0, 0]), (15, [0.2, 0, 0]), (25, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (8, [0, 0.3, 0]), (15, [0.1, -0.4, 0]), (25, [0, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (15, [0.2, 0, 0]), (25, [0, 0, 0])],
        },
    },
    "attack_heavy": {
        "description": "Heavy attack",
        "category": "combat",
        "duration": 35,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (10, [-0.5, 1.2, -1.0]),
                (20, [1.0, -1.0, 0.5]),
                (35, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (10, [0.8, 0, 0]), (20, [0.3, 0, 0]), (35, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (10, [0, 0.4, 0]), (20, [0.15, -0.5, 0]), (35, [0, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (20, [0.3, 0, 0]), (35, [0, 0, 0])],
        },
    },
    "attack_spin": {
        "description": "Spin attack",
        "category": "combat",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (15, [0, 3.14, 0]), (30, [0, 6.28, 0])],
            "upper_arm.R": [(1, [0, 0, -1.2]), (30, [0, 0, -1.2])],
            "upper_arm.L": [(1, [0, 0, 1.2]), (30, [0, 0, 1.2])],
        },
    },
    "attack_uppercut": {
        "description": "Uppercut",
        "category": "combat",
        "duration": 20,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (5, [0.5, 0, 0]),
                (10, [-0.8, 0.3, 0]),
                (20, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (5, [0.8, 0, 0]), (10, [0.3, 0, 0]), (20, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (5, [0.1, 0, 0]), (10, [-0.2, 0, 0]), (20, [0, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (10, [0.2, 0, 0]), (20, [0, 0, 0])],
        },
    },
    "block": {
        "description": "Block",
        "category": "combat",
        "duration": 15,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [(1, [0, 0, 0]), (5, [0.5, 0.5, 0.8]), (15, [0.5, 0.5, 0.8])],
            "upper_arm.R": [(1, [0, 0, 0]), (5, [0.5, -0.5, -0.8]), (15, [0.5, -0.5, -0.8])],
            "forearm.L": [(1, [0, 0, 0]), (5, [1.0, 0, 0]), (15, [1.0, 0, 0])],
            "forearm.R": [(1, [0, 0, 0]), (5, [1.0, 0, 0]), (15, [1.0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (5, [0.1, 0, 0]), (15, [0.1, 0, 0])],
        },
    },
    "parry": {
        "description": "Parry",
        "category": "combat",
        "duration": 12,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [(1, [0.5, -0.5, -0.8]), (6, [0.3, 0.8, -0.3]), (12, [0, 0, 0])],
            "forearm.R": [(1, [1.0, 0, 0]), (6, [0.5, 0.3, 0]), (12, [0, 0, 0])],
            "spine": [(1, [0.1, 0, 0]), (6, [0, -0.2, 0]), (12, [0, 0, 0])],
        },
    },
    "hit_light": {
        "description": "Hit reaction (light)",
        "category": "combat",
        "duration": 15,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (5, [-0.15, 0, 0]), (15, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (5, [-0.2, 0, 0]), (15, [0, 0, 0])],
        },
    },
    "hit_heavy": {
        "description": "Hit reaction (heavy)",
        "category": "combat",
        "duration": 25,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (8, [-0.4, 0, 0]), (25, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (8, [-0.5, 0, 0]), (25, [0, 0, 0])],
            "upper_arm.L": [(1, [0, 0, 0]), (8, [0.3, 0, 0.5]), (25, [0, 0, 0])],
            "upper_arm.R": [(1, [0, 0, 0]), (8, [0.3, 0, -0.5]), (25, [0, 0, 0])],
        },
    },
    "knockdown": {
        "description": "Knockdown",
        "category": "combat",
        "duration": 40,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (10, [-0.5, 0, 0]), (20, [-1.2, 0, 0]), (40, [-1.57, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (20, [0.5, 0, 0]), (40, [0.2, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (20, [0.5, 0, 0]), (40, [0.2, 0, 0])],
        },
    },
    "getup": {
        "description": "Get up",
        "category": "combat",
        "duration": 35,
        "loop": False,
        "keyframes": {
            "spine": [(1, [-1.57, 0, 0]), (15, [-0.8, 0, 0]), (25, [-0.3, 0, 0]), (35, [0, 0, 0])],
            "thigh.L": [(1, [0.2, 0, 0]), (15, [0.8, 0, 0]), (25, [0.3, 0, 0]), (35, [0, 0, 0])],
            "thigh.R": [(1, [0.2, 0, 0]), (15, [0.8, 0, 0]), (25, [0.3, 0, 0]), (35, [0, 0, 0])],
        },
    },
    "death": {
        "description": "Death",
        "category": "combat",
        "duration": 50,
        "loop": False,
        "keyframes": {
            "spine": [
                (1, [0, 0, 0]),
                (15, [-0.3, 0.2, 0]),
                (30, [-0.8, 0.1, 0]),
                (50, [-1.57, 0, 0]),
            ],
            "head": [(1, [0, 0, 0]), (15, [-0.2, 0.3, 0]), (50, [-0.3, 0, 0])],
            "upper_arm.L": [(1, [0, 0, 0]), (30, [0.5, 0, 0.8]), (50, [0.3, 0, 0.5])],
            "upper_arm.R": [(1, [0, 0, 0]), (30, [0.5, 0, -0.8]), (50, [0.3, 0, -0.5])],
            "thigh.L": [(1, [0, 0, 0]), (30, [0.4, 0, 0.2]), (50, [0.2, 0, 0.1])],
            "thigh.R": [(1, [0, 0, 0]), (30, [0.4, 0, -0.2]), (50, [0.2, 0, -0.1])],
        },
    },
    # ==================== Skill Actions ====================
    "cast_spell": {
        "description": "Cast spell",
        "category": "skill",
        "duration": 40,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [
                (1, [0, 0, 0]),
                (15, [0, 0.5, -1.2]),
                (25, [0, 0.5, -1.2]),
                (40, [0, 0, 0]),
            ],
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (15, [0, -0.5, 1.2]),
                (25, [0, -0.5, 1.2]),
                (40, [0, 0, 0]),
            ],
            "forearm.L": [(1, [0, 0, 0]), (15, [0.5, 0, 0]), (25, [0.5, 0, 0]), (40, [0, 0, 0])],
            "forearm.R": [(1, [0, 0, 0]), (15, [0.5, 0, 0]), (25, [0.5, 0, 0]), (40, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (15, [-0.1, 0, 0]), (25, [-0.1, 0, 0]), (40, [0, 0, 0])],
        },
    },
    "cast_fireball": {
        "description": "Throw fireball",
        "category": "skill",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (10, [-0.3, 0.8, -1.0]),
                (20, [0.5, -0.5, 0.3]),
                (30, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (10, [0.8, 0, 0]), (20, [0.2, 0, 0]), (30, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (10, [0, 0.3, 0]), (20, [0, -0.2, 0]), (30, [0, 0, 0])],
        },
    },
    "cast_heal": {
        "description": "Healing cast",
        "category": "skill",
        "duration": 50,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [
                (1, [0, 0, 0]),
                (20, [0, 0, -2.0]),
                (35, [0, 0, -2.0]),
                (50, [0, 0, 0]),
            ],
            "upper_arm.R": [(1, [0, 0, 0]), (20, [0, 0, 2.0]), (35, [0, 0, 2.0]), (50, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (20, [-0.2, 0, 0]), (35, [-0.2, 0, 0]), (50, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (20, [-0.1, 0, 0]), (35, [-0.1, 0, 0]), (50, [0, 0, 0])],
        },
    },
    "charge_power": {
        "description": "Charge power",
        "category": "skill",
        "duration": 60,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [(1, [0, 0, 0]), (30, [0.3, 0, 0.5]), (60, [0.3, 0, 0.5])],
            "upper_arm.R": [(1, [0, 0, 0]), (30, [0.3, 0, -0.5]), (60, [0.3, 0, -0.5])],
            "spine": [(1, [0, 0, 0]), (30, [0.1, 0, 0]), (60, [0.1, 0, 0])],
            "head": [(1, [0, 0, 0]), (30, [-0.1, 0, 0]), (60, [-0.1, 0, 0])],
        },
    },
    "release_power": {
        "description": "Release power",
        "category": "skill",
        "duration": 25,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [(1, [0.3, 0, 0.5]), (10, [0, 0, -1.5]), (25, [0, 0, 0])],
            "upper_arm.R": [(1, [0.3, 0, -0.5]), (10, [0, 0, 1.5]), (25, [0, 0, 0])],
            "spine": [(1, [0.1, 0, 0]), (10, [-0.2, 0, 0]), (25, [0, 0, 0])],
        },
    },
    # ==================== Social/Interaction Actions ====================
    "wave": {
        "description": "Wave",
        "category": "social",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [(1, [0, 0, -1.2]), (30, [0, 0, -1.2])],
            "forearm.R": [
                (1, [0, 0, 0]),
                (8, [0, 0.3, 0]),
                (16, [0, -0.3, 0]),
                (24, [0, 0.3, 0]),
                (30, [0, 0, 0]),
            ],
        },
    },
    "celebrate": {
        "description": "Celebrate",
        "category": "social",
        "duration": 60,
        "loop": False,
        "keyframes": {
            "upper_arm.L": [
                (1, [0, 0, 0]),
                (15, [0, 0, -2.5]),
                (30, [0, 0, -2.3]),
                (45, [0, 0, -2.5]),
                (60, [0, 0, 0]),
            ],
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (15, [0, 0, 2.5]),
                (30, [0, 0, 2.3]),
                (45, [0, 0, 2.5]),
                (60, [0, 0, 0]),
            ],
            "head": [
                (1, [0, 0, 0]),
                (15, [-0.2, 0, 0]),
                (30, [-0.1, 0.1, 0]),
                (45, [-0.2, -0.1, 0]),
                (60, [0, 0, 0]),
            ],
            "spine": [(1, [0, 0, 0]), (20, [-0.1, 0, 0]), (40, [-0.15, 0, 0]), (60, [0, 0, 0])],
        },
    },
    "dance": {
        "description": "Dance",
        "category": "social",
        "duration": 48,
        "loop": True,
        "keyframes": {
            "spine": [
                (1, [0, 0, 0]),
                (12, [0, 0.1, 0]),
                (24, [0, -0.1, 0]),
                (36, [0, 0.1, 0]),
                (48, [0, 0, 0]),
            ],
            "head": [
                (1, [0, 0, 0]),
                (12, [0, 0.15, 0]),
                (24, [0, -0.15, 0]),
                (36, [0, 0.15, 0]),
                (48, [0, 0, 0]),
            ],
            "upper_arm.L": [
                (1, [0, 0, -0.5]),
                (12, [0, 0, -1.0]),
                (24, [0, 0, -0.5]),
                (36, [0, 0, -1.0]),
                (48, [0, 0, -0.5]),
            ],
            "upper_arm.R": [
                (1, [0, 0, 0.5]),
                (12, [0, 0, 1.0]),
                (24, [0, 0, 0.5]),
                (36, [0, 0, 1.0]),
                (48, [0, 0, 0.5]),
            ],
        },
    },
    "sit": {
        "description": "Sit down",
        "category": "social",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "thigh.L": [(1, [0, 0, 0]), (30, [1.5, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (30, [1.5, 0, 0])],
            "shin.L": [(1, [0, 0, 0]), (30, [-1.5, 0, 0])],
            "shin.R": [(1, [0, 0, 0]), (30, [-1.5, 0, 0])],
            "spine": [(1, [0, 0, 0]), (30, [0.2, 0, 0])],
        },
    },
    "bow": {
        "description": "Bow",
        "category": "social",
        "duration": 40,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (15, [0.5, 0, 0]), (25, [0.5, 0, 0]), (40, [0, 0, 0])],
            "spine.001": [(1, [0, 0, 0]), (15, [0.3, 0, 0]), (25, [0.3, 0, 0]), (40, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (15, [0.2, 0, 0]), (25, [0.2, 0, 0]), (40, [0, 0, 0])],
        },
    },
    "salute": {
        "description": "Salute",
        "category": "social",
        "duration": 35,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (12, [0.8, 0.5, 0]),
                (25, [0.8, 0.5, 0]),
                (35, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (12, [1.2, 0, 0]), (25, [1.2, 0, 0]), (35, [0, 0, 0])],
            "spine": [(1, [0, 0, 0]), (12, [0.05, 0, 0]), (25, [0.05, 0, 0]), (35, [0, 0, 0])],
        },
    },
    "point": {
        "description": "Point",
        "category": "social",
        "duration": 25,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [(1, [0, 0, 0]), (10, [0.3, 0, -0.8]), (25, [0.3, 0, -0.8])],
            "forearm.R": [(1, [0, 0, 0]), (10, [0.2, 0, 0]), (25, [0.2, 0, 0])],
        },
    },
    "pickup": {
        "description": "Pick up item",
        "category": "interaction",
        "duration": 30,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (12, [0.6, 0, 0]), (20, [0.6, 0, 0]), (30, [0, 0, 0])],
            "thigh.L": [(1, [0, 0, 0]), (12, [0.4, 0, 0]), (20, [0.4, 0, 0]), (30, [0, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (12, [0.4, 0, 0]), (20, [0.4, 0, 0]), (30, [0, 0, 0])],
            "upper_arm.R": [(1, [0, 0, 0]), (12, [0.8, 0, 0]), (20, [0.8, 0, 0]), (30, [0, 0, 0])],
        },
    },
    "use_item": {
        "description": "Use item",
        "category": "interaction",
        "duration": 40,
        "loop": False,
        "keyframes": {
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (10, [0.5, 0.3, -0.3]),
                (25, [0.5, 0.3, -0.3]),
                (40, [0, 0, 0]),
            ],
            "forearm.R": [(1, [0, 0, 0]), (10, [0.8, 0, 0]), (25, [0.8, 0, 0]), (40, [0, 0, 0])],
            "head": [(1, [0, 0, 0]), (10, [0.1, 0, 0]), (25, [0.1, 0, 0]), (40, [0, 0, 0])],
        },
    },
    "open_chest": {
        "description": "Open chest",
        "category": "interaction",
        "duration": 45,
        "loop": False,
        "keyframes": {
            "spine": [(1, [0, 0, 0]), (15, [0.3, 0, 0]), (30, [0.3, 0, 0]), (45, [0, 0, 0])],
            "upper_arm.L": [
                (1, [0, 0, 0]),
                (15, [0.5, 0, 0.5]),
                (30, [0.3, 0, 0.3]),
                (45, [0, 0, 0]),
            ],
            "upper_arm.R": [
                (1, [0, 0, 0]),
                (15, [0.5, 0, -0.5]),
                (30, [0.3, 0, -0.3]),
                (45, [0, 0, 0]),
            ],
            "thigh.L": [(1, [0, 0, 0]), (15, [0.3, 0, 0]), (30, [0.3, 0, 0]), (45, [0, 0, 0])],
            "thigh.R": [(1, [0, 0, 0]), (15, [0.3, 0, 0]), (30, [0.3, 0, 0]), (45, [0, 0, 0])],
        },
    },
}


def handle_apply(params: dict[str, Any]) -> dict[str, Any]:
    """Apply preset animation"""
    armature_name = params.get("armature_name", "")
    preset = params.get("preset", "idle")
    speed = params.get("speed", 1.0)
    loop = params.get("loop", True)

    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    preset_config = ANIMATION_PRESETS.get(preset)
    if not preset_config:
        return {
            "success": False,
            "error": {"code": "PRESET_NOT_FOUND", "message": f"Preset not found: {preset}"},
        }

    # Create action
    action_name = f"{armature_name}_{preset}"
    action = bpy.data.actions.new(name=action_name)

    # Associate action with armature
    if not armature_obj.animation_data:
        armature_obj.animation_data_create()
    armature_obj.animation_data.action = action

    # Enter pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode="POSE")

    # Apply keyframes
    keyframes = preset_config["keyframes"]
    duration = int(preset_config["duration"] / speed)

    for bone_name, frames in keyframes.items():
        pose_bone = armature_obj.pose.bones.get(bone_name)
        if not pose_bone:
            continue

        for frame, rotation in frames:
            adjusted_frame = int(frame / speed)
            pose_bone.rotation_euler = rotation
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=adjusted_frame)

    # Set loop
    if loop:
        for fcurve in action.fcurves:
            for modifier in fcurve.modifiers:
                fcurve.modifiers.remove(modifier)
            fcurve.modifiers.new(type="CYCLES")

    bpy.ops.object.mode_set(mode="OBJECT")

    # Set timeline range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = duration

    return {
        "success": True,
        "data": {"preset": preset, "action_name": action_name, "duration": duration},
    }


def handle_action_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create action"""
    action_name = params.get("action_name")
    armature_name = params.get("armature_name", "")
    frame_start = params.get("frame_start", 1)
    frame_end = params.get("frame_end", 60)

    # Create action
    action = bpy.data.actions.new(name=action_name)
    action.frame_range = (frame_start, frame_end)

    # If armature is specified, associate action
    if armature_name:
        armature_obj = bpy.data.objects.get(armature_name)
        if armature_obj and armature_obj.type == "ARMATURE":
            if not armature_obj.animation_data:
                armature_obj.animation_data_create()
            armature_obj.animation_data.action = action

    return {"success": True, "data": {"action_name": action.name}}


def handle_nla_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add NLA strip"""
    object_name = params.get("object_name", "")
    action_name = params.get("action_name", "")
    track_name = params.get("track_name", "NlaTrack")
    start_frame = params.get("start_frame", 1)
    blend_type = params.get("blend_type", "REPLACE")
    scale = params.get("scale", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    action = bpy.data.actions.get(action_name)
    if not action:
        return {
            "success": False,
            "error": {"code": "ACTION_NOT_FOUND", "message": f"Action not found: {action_name}"},
        }

    # Ensure animation data exists
    if not obj.animation_data:
        obj.animation_data_create()

    # Create or get NLA track
    track = obj.animation_data.nla_tracks.new()
    track.name = track_name

    # Add strip
    strip = track.strips.new(action_name, start_frame, action)
    strip.blend_type = blend_type
    strip.scale = scale

    return {"success": True, "data": {"track_name": track_name, "strip_name": strip.name}}


def handle_follow_path(params: dict[str, Any]) -> dict[str, Any]:
    """Path animation"""
    object_name = params.get("object_name", "")
    path_name = params.get("path_name", "")
    duration = params.get("duration", 100)
    follow_rotation = params.get("follow_rotation", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    path = bpy.data.objects.get(path_name)
    if not path or path.type != "CURVE":
        return {
            "success": False,
            "error": {"code": "PATH_NOT_FOUND", "message": f"Path not found: {path_name}"},
        }

    # Add follow path constraint
    constraint = obj.constraints.new("FOLLOW_PATH")
    constraint.target = path
    constraint.use_curve_follow = follow_rotation

    # Set up path animation
    path.data.use_path = True
    path.data.path_duration = duration

    # Animate offset
    constraint.offset_factor = 0
    constraint.keyframe_insert(data_path="offset_factor", frame=1)
    constraint.offset_factor = 1
    constraint.keyframe_insert(data_path="offset_factor", frame=duration)

    return {"success": True, "data": {"duration": duration}}


def handle_bake(params: dict[str, Any]) -> dict[str, Any]:
    """Bake animation"""
    object_name = params.get("object_name", "")
    frame_start = params.get("frame_start", 1)
    frame_end = params.get("frame_end", 250)
    params.get("bake_types", ["LOCATION", "ROTATION", "SCALE"])
    clear_constraints = params.get("clear_constraints", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # If armature, enter pose mode
    if obj.type == "ARMATURE":
        bpy.ops.object.mode_set(mode="POSE")
        bpy.ops.pose.select_all(action="SELECT")

        bpy.ops.nla.bake(
            frame_start=frame_start,
            frame_end=frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=clear_constraints,
            bake_types={"POSE"},
        )

        bpy.ops.object.mode_set(mode="OBJECT")
    else:
        bpy.ops.nla.bake(
            frame_start=frame_start,
            frame_end=frame_end,
            only_selected=True,
            visual_keying=True,
            clear_constraints=clear_constraints,
            bake_types={"OBJECT"},
        )

    return {"success": True, "data": {"frames_baked": frame_end - frame_start + 1}}
