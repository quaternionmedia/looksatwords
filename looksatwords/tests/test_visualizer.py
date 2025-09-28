from looksatwords.visualizer import Visualizer
import tempfile
import os


def test_visualizer():
    """Test basic visualizer initialization and setup."""
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test visualizer creation with custom output path
        visualizer = Visualizer(output_path=temp_dir + '/')
        
        # Check that visualizer was created properly
        assert visualizer is not None
        assert visualizer.output_path == temp_dir + '/'
        assert hasattr(visualizer, 'df')
        assert hasattr(visualizer, 'folder_path')
        assert hasattr(visualizer, 'table_name')
        
        # Test that the output directory exists
        assert os.path.exists(visualizer.output_path)
        
        # Test that visualizer inherits from Analyzer (has analyzer methods)
        assert hasattr(visualizer, 'build_words_df')
        assert hasattr(visualizer, 'preprocess')
        assert hasattr(visualizer, 'analyze')
        
        # Test that visualizer has its specific methods
        assert hasattr(visualizer, 'visualize')
        assert hasattr(visualizer, 'make_plots')
        
        print("✅ Visualizer test passed - basic functionality verified")

