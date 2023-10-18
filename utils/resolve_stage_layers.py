import logging
import os
import subprocess
import tempfile

from pxr import Sdf, Usd

logging.basicConfig(level=logging.INFO)


def collect_layer_paths_from_prim(prim):
    """Collects all unique layer paths from a given prim."""
    return {prim_spec.layer.realPath for prim_spec in prim.GetPrimStack()}


def collect_all_layer_paths(stage):
    """Collects all unique layer paths from all prims in a given stage."""
    return {
        layer_path
        for prim in stage.Traverse()
        for layer_path in collect_layer_paths_from_prim(prim)
    }


def convert_to_ascii(layer_path, tmp_dir, conversion_dict):
    """Converts a given USD file to ASCII using usdcat if it's not already in ASCII."""
    output_path = os.path.join(tmp_dir, os.path.basename(layer_path))
    if output_path.endswith(".usdc") or output_path.endswith(".usdz"):
        output_path = output_path.rsplit(".", 1)[0] + ".usda"

    layer = Sdf.Layer.FindOrOpen(layer_path)
    if layer and not layer_path.endswith(".usda"):
        logging.info(f"Converting {layer_path} to ASCII...")
        subprocess.run(["usdcat", "-o", output_path, layer_path])
        conversion_dict[layer_path] = output_path
    else:
        logging.info(
            f"{layer_path} is already in ASCII format or couldn't be opened.")


def resolve_all_layers(
    filepath,
    signal_progress_update,
    progress_range=(
        0,
        20)):
    """Main function to collect and print all unique layer paths from a USD stage."""
    stage = Usd.Stage.Open(filepath)
    all_layer_paths = collect_all_layer_paths(stage)

    tmp_dir = tempfile.mkdtemp(prefix="usd_ascii_")
    logging.info(f"Temporary directory created: {tmp_dir}")

    conversion_dict = {}
    total_layers = len(all_layer_paths)
    logging.info(f"All collected layers ({total_layers}):")
    processed_layers = 0
    for layer_path in all_layer_paths:
        logging.info(layer_path)
        convert_to_ascii(layer_path, tmp_dir, conversion_dict)

        # Update progress
        processed_layers += 1
        progress_percentage = int(
            progress_range[0]
            + (
                (processed_layers / total_layers)
                * (progress_range[1] - progress_range[0])
            )
        )
        signal_progress_update.emit(
            progress_percentage,
            f"Resolving Stage: {processed_layers}/{total_layers} layers ({progress_percentage}%)",
        )

    final_paths = [conversion_dict.get(path, path) for path in all_layer_paths]

    logging.info(f"\nFinal paths ({len(final_paths)}):")
    for path in final_paths:
        logging.info(path)

    return final_paths
