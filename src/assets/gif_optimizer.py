import os
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageSequence
import math


@dataclass
class OptimizationConfig:
    """Configuration for GIF optimization"""

    target_size_kb: int = 100
    max_width: int = 800
    max_height: int = 600
    quality: int = 85
    colors: int = 256
    optimize: bool = True
    preserve_animation: bool = True
    backup_original: bool = True


class GifOptimizationError(Exception):
    """Custom exception for GIF optimization errors"""

    pass


class GifOptimizer:
    """
    Production-level GIF optimizer with advanced features
    """

    def __init__(
        self,
        input_folder: str,
        target_size_kb: int = 100,
        output_folder: Optional[str] = None,
        config: Optional[OptimizationConfig] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ):
        """
        Initialize the GIF optimizer

        Args:
            input_folder: Path to folder containing GIF files
            target_size_kb: Target file size in KB
            output_folder: Output folder (defaults to input_folder/optimized)
            config: Optimization configuration
            progress_callback: Callback function for progress updates
        """
        self.input_folder = Path(input_folder)
        self.target_size_kb = target_size_kb
        self.output_folder = (
            Path(output_folder) if output_folder else self.input_folder / "optimized"
        )
        self.config = config or OptimizationConfig(target_size_kb=target_size_kb)
        self.progress_callback = progress_callback

        # Setup logging
        self._setup_logging()

        # Ensure output directory exists
        self.output_folder.mkdir(exist_ok=True)

        # Statistics
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "total_original_size": 0,
            "total_optimized_size": 0,
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("gif_optimizer.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _update_progress(self, percentage: int):
        """Update progress callback if provided"""
        if self.progress_callback:
            self.progress_callback(percentage)

    def _get_gif_files(self) -> List[Path]:
        """Get all GIF files from input folder"""
        gif_files = list(self.input_folder.glob("*.gif"))
        gif_files.extend(self.input_folder.glob("*.GIF"))
        return sorted(gif_files)

    def _calculate_scale_factor(self, original_size: int, target_size: int) -> float:
        """Calculate optimal scale factor based on file size"""
        if original_size <= target_size:
            return 1.0

        # Estimate scale factor based on size ratio
        size_ratio = target_size / original_size
        scale_factor = math.sqrt(
            size_ratio
        )  # Square root because area scales quadratically

        # Clamp to reasonable bounds
        return max(0.1, min(1.0, scale_factor))

    def _optimize_single_gif(self, input_path: Path) -> bool:
        """
        Optimize a single GIF file

        Args:
            input_path: Path to input GIF file

        Returns:
            bool: True if optimization was successful
        """
        try:
            output_path = self.output_folder / f"optimized_{input_path.name}"

            # Get original file size
            original_size = input_path.stat().st_size / 1024  # Convert to KB
            self.stats["total_original_size"] += original_size

            self.logger.info(f"Processing: {input_path.name} ({original_size:.1f} KB)")

            with Image.open(input_path) as img:
                # Check if animated
                is_animated = hasattr(img, "n_frames") and img.n_frames > 1

                if is_animated and self.config.preserve_animation:
                    success = self._optimize_animated_gif(
                        img, output_path, original_size
                    )
                else:
                    success = self._optimize_static_gif(img, output_path, original_size)

                if success:
                    optimized_size = output_path.stat().st_size / 1024
                    self.stats["total_optimized_size"] += optimized_size
                    compression_ratio = (1 - optimized_size / original_size) * 100

                    self.logger.info(
                        f"Optimized: {output_path.name} "
                        f"({original_size:.1f} KB → {optimized_size:.1f} KB, "
                        f"{compression_ratio:.1f}% reduction)"
                    )

                    self.stats["successful"] += 1
                    return True
                else:
                    self.stats["failed"] += 1
                    return False

        except Exception as e:
            self.logger.error(f"Error processing {input_path.name}: {str(e)}")
            self.stats["failed"] += 1
            return False

    def _optimize_static_gif(
        self, img: Image.Image, output_path: Path, original_size: int
    ) -> bool:
        """Optimize static GIF"""
        try:
            # Calculate optimal parameters
            scale_factor = self._calculate_scale_factor(
                original_size, self.target_size_kb
            )

            # Resize if needed
            if scale_factor < 1.0:
                new_size = (
                    int(img.width * scale_factor),
                    int(img.height * scale_factor),
                )
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save with optimization
            img.save(
                output_path,
                "GIF",
                optimize=self.config.optimize,
                colors=self.config.colors,
                quality=self.config.quality,
            )

            return True

        except Exception as e:
            self.logger.error(f"Error optimizing static GIF: {str(e)}")
            return False

    def _optimize_animated_gif(
        self, img: Image.Image, output_path: Path, original_size: int
    ) -> bool:
        """Optimize animated GIF"""
        try:
            # Calculate optimal parameters
            scale_factor = self._calculate_scale_factor(
                original_size, self.target_size_kb
            )

            frames = []
            durations = []

            # Process each frame
            for frame_idx in range(img.n_frames):
                img.seek(frame_idx)

                # Get frame duration
                duration = img.info.get("duration", 100)
                durations.append(duration)

                # Resize frame if needed
                if scale_factor < 1.0:
                    new_size = (
                        int(img.width * scale_factor),
                        int(img.height * scale_factor),
                    )
                    frame = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    frame = img.copy()

                frames.append(frame)

            # Save optimized animated GIF
            if frames:
                frames[0].save(
                    output_path,
                    "GIF",
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=img.info.get("loop", 0),
                    optimize=self.config.optimize,
                    colors=self.config.colors,
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error optimizing animated GIF: {str(e)}")
            return False

    def process_folder(self) -> Dict[str, Any]:
        """
        Process all GIF files in the input folder

        Returns:
            Dict containing processing statistics
        """
        self.logger.info(f"Starting GIF optimization for folder: {self.input_folder}")
        self.logger.info(f"Target size: {self.target_size_kb} KB")
        self.logger.info(f"Output folder: {self.output_folder}")

        gif_files = self._get_gif_files()

        if not gif_files:
            self.logger.warning("No GIF files found in input folder")
            return self.stats

        self.logger.info(f"Found {len(gif_files)} GIF files to process")

        # Process files with progress updates
        for idx, gif_file in enumerate(gif_files):
            self.stats["processed"] += 1

            # Update progress
            progress = int((idx + 1) / len(gif_files) * 100)
            self._update_progress(progress)

            # Process the file
            self._optimize_single_gif(gif_file)

        # Final progress update
        self._update_progress(100)

        # Log final statistics
        self._log_final_stats()

        return self.stats

    def _log_final_stats(self):
        """Log final processing statistics"""
        total_savings = (
            self.stats["total_original_size"] - self.stats["total_optimized_size"]
        )
        savings_percentage = (
            (total_savings / self.stats["total_original_size"] * 100)
            if self.stats["total_original_size"] > 0
            else 0
        )

        self.logger.info("=" * 50)
        self.logger.info("OPTIMIZATION COMPLETED")
        self.logger.info("=" * 50)
        self.logger.info(f"Files processed: {self.stats['processed']}")
        self.logger.info(f"Successful: {self.stats['successful']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(
            f"Original total size: {self.stats['total_original_size']:.1f} KB"
        )
        self.logger.info(
            f"Optimized total size: {self.stats['total_optimized_size']:.1f} KB"
        )
        self.logger.info(
            f"Total savings: {total_savings:.1f} KB ({savings_percentage:.1f}%)"
        )
        self.logger.info("=" * 50)


# Backward compatibility functions
def compress_gif(input_path, output_path, optimize=True, colors=256):
    """Legacy function for backward compatibility"""
    optimizer = GifOptimizer(
        input_folder=os.path.dirname(input_path),
        config=OptimizationConfig(colors=colors, optimize=optimize),
    )
    return optimizer._optimize_single_gif(Path(input_path))


def resize_gif(input_path, output_path, scale_factor=0.5):
    """Legacy function for backward compatibility"""
    config = OptimizationConfig()
    config.max_width = int(800 * scale_factor)
    config.max_height = int(600 * scale_factor)

    optimizer = GifOptimizer(input_folder=os.path.dirname(input_path), config=config)
    return optimizer._optimize_single_gif(Path(input_path))
