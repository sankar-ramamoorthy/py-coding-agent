"""Tests for resolve_safe_path's real path containment (fixes the ISS-002 prefix bug)."""

import os
import sys

import pytest

from py_mono.utils import path_utils as path_utils_module


@pytest.fixture
def fake_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(path_utils_module, "WORKSPACE_ROOT", workspace.resolve())
    monkeypatch.setattr(path_utils_module, "ADDITIONAL_ALLOWED_PATHS", [])
    return workspace


def test_valid_in_workspace_path_still_resolves(fake_workspace):
    result = path_utils_module.resolve_safe_path("subdir/file.txt")
    assert result == (fake_workspace / "subdir" / "file.txt").resolve()


def test_workspace_root_itself_resolves(fake_workspace):
    result = path_utils_module.resolve_safe_path(".")
    assert result == fake_workspace.resolve()


def test_dotdot_traversal_is_rejected(fake_workspace):
    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path("../etc/passwd")


def test_sibling_prefix_collision_is_rejected(tmp_path, monkeypatch):
    # Reproduces the audit's own literal probe: a sibling dir whose NAME
    # textually starts with the workspace root's name must not pass.
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    evil = tmp_path / "workspace_evil"
    evil.mkdir()
    monkeypatch.setattr(path_utils_module, "WORKSPACE_ROOT", workspace.resolve())
    monkeypatch.setattr(path_utils_module, "ADDITIONAL_ALLOWED_PATHS", [])

    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path("../workspace_evil")


def test_absolute_path_escape_is_rejected(fake_workspace, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path(str(outside))


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "Symlink creation on Windows requires Developer Mode or an elevated "
        "process (SeCreateSymbolicLinkPrivilege); not reliable in this dev "
        "environment's default test run. Covered on POSIX / in the Linux "
        "container where the app actually runs."
    ),
)
def test_symlink_escape_is_rejected(fake_workspace, tmp_path):
    outside_target = tmp_path / "outside_dir"
    outside_target.mkdir()
    (outside_target / "secret.txt").write_text("secret")

    link = fake_workspace / "escape_link"
    os.symlink(outside_target, link, target_is_directory=True)

    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path("escape_link/secret.txt")


def test_path_inside_additional_allowed_directory_is_accepted(fake_workspace, tmp_path, monkeypatch):
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    monkeypatch.setattr(path_utils_module, "ADDITIONAL_ALLOWED_PATHS", [extra_dir.resolve()])

    target = extra_dir / "file.txt"
    result = path_utils_module.resolve_safe_path(str(target))
    assert result == target.resolve()


def test_path_outside_workspace_and_additional_paths_is_rejected(fake_workspace, tmp_path, monkeypatch):
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    monkeypatch.setattr(path_utils_module, "ADDITIONAL_ALLOWED_PATHS", [extra_dir.resolve()])

    unrelated = tmp_path / "unrelated" / "file.txt"
    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path(str(unrelated))


def test_empty_additional_allowed_paths_is_identical_to_workspace_only(fake_workspace, tmp_path):
    # ADDITIONAL_ALLOWED_PATHS is [] via the fake_workspace fixture — confirms
    # default (empty) behavior matches the pre-existing workspace-only case.
    with pytest.raises(ValueError, match="outside allowed directories"):
        path_utils_module.resolve_safe_path("../workspace_evil")
