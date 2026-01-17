"""Tests for the HUD module."""
import json
from pathlib import Path
from looksatwords.hud import HUD, parse_json_to_tree
from rich.tree import Tree


def test_parse_json_to_tree():
    """Test that JSON parsing creates a tree structure."""
    test_json = {
        "items": [1, 2, 3],
        "users": [{"name": "test"}],
        "table": "should_be_ignored"
    }
    tree = parse_json_to_tree(test_json)
    assert isinstance(tree, Tree)


def test_parse_json_to_tree_with_custom_tree():
    """Test JSON parsing with custom tree."""
    custom_tree = Tree("custom_root")
    test_json = {"data": [1, 2, 3, 4, 5]}
    result = parse_json_to_tree(test_json, custom_tree)
    assert isinstance(result, Tree)


def test_hud_init():
    """Test HUD initialization."""
    hud = HUD()
    assert hud.title == "Looking at words..."
    assert hud.refresh_per_second == 4


def test_hud_init_custom_title():
    """Test HUD initialization with custom title."""
    custom_title = "Custom HUD Title"
    hud = HUD(title=custom_title)
    assert hud.title == custom_title


def test_hud_make_layout():
    """Test HUD layout creation."""
    hud = HUD()
    layout = hud.make_layout()
    assert layout is not None


def test_hud_context_manager():
    """Test HUD as context manager."""
    with HUD() as hud:
        assert hud is not None
        # Just verify context manager works without errors


def test_hud_show_db_nonexistent():
    """Test show_db with nonexistent file."""
    hud = HUD()
    # Should not raise error with nonexistent file
    hud.show_db("nonexistent_file.json")


def test_hud_show_db_with_json(tmp_path):
    """Test show_db with actual JSON file."""
    # Create temporary JSON file
    test_db = tmp_path / "test_db.json"
    test_data = {
        "_default": {
            "1": {"title": "Test", "description": "Test data"}
        }
    }
    test_db.write_text(json.dumps(test_data))
    
    hud = HUD()
    # Should not raise error
    hud.show_db(str(test_db))
