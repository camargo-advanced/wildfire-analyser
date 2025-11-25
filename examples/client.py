# client.py

import logging
import os

from wildfire_analyser import PostFireAssessment

logger = logging.getLogger(__name__)


def main():
    # Configure global logging format and level
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger.info("Client starts")

    try:
        # Path to the GeoJSON polygon used as the Region of Interest (ROI)
        geojson_path = os.path.join("polygons", "eejatai.geojson")

        # Initialize the wildfire assessment processor with date range
        runner = PostFireAssessment(geojson_path, "2024-09-01", "2024-11-08", 
                                    deliverables=[
                                        #"rgb_pre_fire",
                                        #"rgb_post_fire",
                                        "ndvi_pre_fire",
                                        "ndvi_post_fire",
                                    ])

        # Run the analysis, which returns a dictionary with binary GeoTIFFs
        result = runner.run_analysis()
        logger.info("run_analysis() complete")

        # Save each output (RBR, BEFORE, AFTER) to local files
        # The loop avoids duplicated code and makes it easier to add more outputs later
        for key, item in result.items():
            # item["filename"] contains the file name
            # item["data"] contains the binary GeoTIFF bytes
            with open(item["filename"], "wb") as f:
                f.write(item["data"])
            logger.info(f"Saved file: {item['filename']}")

        logger.info("Client ends")

    except Exception as e:
        logger.exception("Unexpected error during processing")

# Entry point
main()
