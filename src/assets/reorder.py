import os


def rename_file(old_name):
    # Extract the main part of the filename and the extension
    main_part, extension = os.path.splitext(old_name)

    # Split the main part into sections based on '_'
    parts = main_part.split("_")

    # Extract the initial order number and the year
    order = parts[0]
    year = parts[1]

    # The new order number should be the initial number, formatted with leading zero if necessary
    new_order = f"{int(order):02}"

    # Middle parts (from year to the last but one segment)
    middle_parts = parts[2:-1]

    # Construct the new name
    new_name = f"{year}_" + "_".join(middle_parts) + f"_{new_order}{extension}"
    return new_name


def reorder_images(root_folder):
    # Walk through all directories and subdirectories starting from the root
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Filter out files to only include images
        image_files = [
            f
            for f in filenames
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
        ]

        # Sort files if necessary
        image_files.sort()

        # Rename each image file
        for filename in image_files:
            # Create the new file name
            new_name = rename_file(filename)

            # Define the old and new file paths
            old_file = os.path.join(dirpath, filename)
            new_file = os.path.join(dirpath, new_name)

            # Check if new file name already exists
            if (
                old_file != new_file
            ):  # Check to ensure we're not trying to rename a file to its current name
                if os.path.exists(new_file):
                    print(f"Skipping {filename}: {new_file} already exists.")
                    continue

                # Try renaming the file and handle exceptions
                try:
                    os.rename(old_file, new_file)
                    print(f"Renamed '{filename}' to '{new_name}' in {dirpath}")
                except OSError as e:
                    print(f"Error renaming {filename} to {new_name} in {dirpath}: {e}")
            else:
                print(f"No renaming needed for {filename} in {dirpath}.")
