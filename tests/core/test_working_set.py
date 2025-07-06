#!/usr/bin/env python3
"""Unit tests for the working_set module"""

import pytest
import tempfile
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.monitoring.working_set import WorkingSetManager


class TestWorkingSetManager:
    """Test the WorkingSetManager class"""
    
    def test_working_set_manager_creation(self):
        """Test creating a WorkingSetManager instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            assert manager.working_set_dir == Path(temp_dir)
            # Directory should be created automatically
            assert Path(temp_dir).exists()
            
    def test_working_set_manager_creates_directory(self):
        """Test that WorkingSetManager creates directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "nested" / "working_set"
            manager = WorkingSetManager(str(nested_dir))
            
            assert nested_dir.exists()
            assert manager.working_set_dir == nested_dir
            
    def test_ensure_directory_structure(self):
        """Test ensuring directory structure creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Ensure directory structure
            manager.ensure_directory_structure()
            
            # Check that subdirectories exist
            assert (Path(temp_dir) / "tests").exists()
            assert (Path(temp_dir) / "artifacts").exists()
            assert (Path(temp_dir) / "reports").exists()
            
    def test_ensure_directory_structure_existing(self):
        """Test ensuring directory structure when it already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Call ensure_directory_structure multiple times
            manager.ensure_directory_structure()
            manager.ensure_directory_structure()
            
            # Should not raise any errors and directories should exist
            assert (Path(temp_dir) / "tests").exists()
            assert (Path(temp_dir) / "artifacts").exists()
            assert (Path(temp_dir) / "reports").exists()
            
    def test_create_test_file(self):
        """Test creating a test file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            test_content = """def test_example():
    assert 1 + 1 == 2"""
            
            file_path = manager.create_test_file("test_sample", test_content)
            
            assert file_path.exists()
            assert file_path.name == "test_sample.py"
            assert file_path.parent == Path(temp_dir)
            
            # Check content
            with open(file_path, 'r') as f:
                content = f.read()
            assert "def test_example():" in content
            assert "assert 1 + 1 == 2" in content
            
    def test_create_test_file_overwrite(self):
        """Test that creating a test file overwrites existing file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Create first file
            content1 = "def test_first(): pass"
            file_path1 = manager.create_test_file("test_sample", content1)
            
            with open(file_path1, 'r') as f:
                assert "test_first" in f.read()
                
            # Create file with same name
            content2 = "def test_second(): pass"
            file_path2 = manager.create_test_file("test_sample", content2)
            
            # Should be the same path
            assert file_path1 == file_path2
            
            # Should have new content
            with open(file_path2, 'r') as f:
                content = f.read()
                assert "test_second" in content
                assert "test_first" not in content
                
    def test_list_test_files_empty(self):
        """Test listing test files when directory is empty"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            test_files = manager.list_test_files()
            assert test_files == []
            
    def test_list_test_files(self):
        """Test listing test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Create some test files
            manager.create_test_file("test_one", "def test_one(): pass")
            manager.create_test_file("test_two", "def test_two(): pass")
            manager.create_test_file("test_three", "def test_three(): pass")
            
            # Create a non-test file (should be ignored by list_test_files)
            non_test_file = Path(temp_dir) / "not_a_test.py"
            non_test_file.write_text("def regular_function(): pass")
            
            # Create a non-Python file
            other_file = Path(temp_dir) / "test_readme.txt"
            other_file.write_text("This is a readme")
            
            test_files = manager.list_test_files()
            
            # Should only include test_*.py files
            assert len(test_files) == 3
            
            test_names = [f.name for f in test_files]
            assert "test_one.py" in test_names
            assert "test_two.py" in test_names
            assert "test_three.py" in test_names
            
    def test_list_test_files_sorted(self):
        """Test that test files are listed in sorted order"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Create files in non-alphabetical order
            manager.create_test_file("test_zebra", "pass")
            manager.create_test_file("test_alpha", "pass")
            manager.create_test_file("test_beta", "pass")
            
            test_files = manager.list_test_files()
            test_names = [f.name for f in test_files]
            
            # Should be sorted alphabetically
            assert test_names == sorted(test_names)
            
    def test_remove_test_file_existing(self):
        """Test removing an existing test file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Create a test file
            file_path = manager.create_test_file("test_sample", "def test(): pass")
            assert file_path.exists()
            
            # Remove the file
            result = manager.remove_test_file("test_sample")
            assert result is True
            assert not file_path.exists()
            
    def test_remove_test_file_nonexistent(self):
        """Test removing a non-existent test file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Try to remove non-existent file
            result = manager.remove_test_file("nonexistent_test")
            assert result is False
            
    def test_clean_working_set(self):
        """Test cleaning the working set"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Create some files
            manager.create_test_file("test_one", "pass")
            manager.create_test_file("test_two", "pass")
            other_file = Path(temp_dir) / "other_file.txt"
            other_file.write_text("content")
            
            # Clean working set
            manager.clean_working_set()
            
            # Directory should exist but be empty
            assert manager.working_set_dir.exists()
            assert len(list(manager.working_set_dir.iterdir())) == 0
            
    def test_get_working_set_size(self):
        """Test getting working set size"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Initially should be empty
            assert manager.get_working_set_size() == 0
            
            # Add some files
            manager.create_test_file("test_one", "pass")
            manager.create_test_file("test_two", "pass")
            
            assert manager.get_working_set_size() == 2
            
    def test_create_metadata_file(self):
        """Test creating a metadata file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            metadata = {
                "version": "1.0",
                "created": "2024-01-01",
                "tests": ["test_one", "test_two"]
            }
            
            file_path = manager.create_metadata_file(metadata)
            
            assert file_path.exists()
            assert file_path.name == "metadata.json"
            
            # Check content
            with open(file_path, 'r') as f:
                loaded_metadata = json.load(f)
            assert loaded_metadata == metadata
            
    def test_read_metadata_existing(self):
        """Test reading existing metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            metadata = {"version": "1.0", "test": True}
            manager.create_metadata_file(metadata)
            
            loaded_metadata = manager.read_metadata()
            assert loaded_metadata == metadata
            
    def test_read_metadata_nonexistent(self):
        """Test reading non-existent metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            metadata = manager.read_metadata()
            assert metadata is None
            
    def test_get_working_set_path(self):
        """Test getting the working set path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            path = manager.get_working_set_path()
            assert path == Path(temp_dir)


class TestWorkingSetManagerIntegration:
    """Integration tests for WorkingSetManager"""
    
    def test_complete_workflow(self):
        """Test a complete workflow with the WorkingSetManager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Initialize directory structure
            manager.ensure_directory_structure()
            
            # Create metadata
            metadata = {
                "project": "test_project",
                "version": "1.0.0",
                "created": "2024-01-01"
            }
            manager.create_metadata_file(metadata)
            
            # Create some test files
            test_content_1 = """def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2"""
            
            test_content_2 = """def test_multiplication():
    assert 3 * 4 == 12"""
            
            file1 = manager.create_test_file("test_math_basic", test_content_1)
            file2 = manager.create_test_file("test_math_advanced", test_content_2)
            
            # Verify files exist
            assert file1.exists()
            assert file2.exists()
            
            # List all test files
            test_files = manager.list_test_files()
            assert len(test_files) == 2
            
            # Check working set size
            size = manager.get_working_set_size()
            assert size >= 5  # 2 test files + metadata + 3 subdirs
            
            # Read metadata
            loaded_metadata = manager.read_metadata()
            assert loaded_metadata["project"] == "test_project"
            
            # Remove one file
            success = manager.remove_test_file("test_math_basic")
            assert success
            assert not file1.exists()
            
            # Verify remaining files
            test_files = manager.list_test_files()
            assert len(test_files) == 1
            assert test_files[0].name == "test_math_advanced.py"
            
            # Clean everything
            manager.clean_working_set()
            assert manager.get_working_set_size() == 0
            
    def test_metadata_persistence(self):
        """Test that metadata persists across manager instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manager and metadata
            manager1 = WorkingSetManager(temp_dir)
            metadata = {"test": "data", "version": 1}
            manager1.create_metadata_file(metadata)
            
            # Create new manager instance for same directory
            manager2 = WorkingSetManager(temp_dir)
            loaded_metadata = manager2.read_metadata()
            
            assert loaded_metadata == metadata
            
    def test_concurrent_file_operations(self):
        """Test that file operations work correctly when called rapidly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkingSetManager(temp_dir)
            
            # Rapidly create and remove files
            for i in range(10):
                file_name = f"test_rapid_{i}"
                content = f"def test_{i}(): assert {i} == {i}"
                
                # Create
                file_path = manager.create_test_file(file_name, content)
                assert file_path.exists()
                
                # List (should include this file)
                test_files = manager.list_test_files()
                file_names = [f.name for f in test_files]
                assert f"{file_name}.py" in file_names
                
                # Remove every other file
                if i % 2 == 0:
                    success = manager.remove_test_file(file_name)
                    assert success
                    assert not file_path.exists()
                    
            # Should have 5 files remaining
            final_test_files = manager.list_test_files()
            assert len(final_test_files) == 5


if __name__ == '__main__':
    pytest.main([__file__])