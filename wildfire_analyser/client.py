# client.py
import logging
import os
from dotenv import load_dotenv 

from wildfire_analyser import PostFireAssessment, Deliverable, FireSeverity

logger = logging.getLogger(__name__)


def main():
    # Configure global logging format and level
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger.info("Client starts")

    try:
        # Load the local .env file
        load_dotenv()

        # Read the environment variable from .env
        gee_key_json = os.getenv("GEE_PRIVATE_KEY_JSON")
        if gee_key_json is None:
            raise ValueError("GEE_PRIVATE_KEY_JSON environment variable is not set in .env")

        # Path to the GeoJSON polygon used as the Region of Interest (ROI)
        geojson_path = os.path.join("polygons", "eejatai.geojson")

        # Initialize the wildfire assessment processor with date range
        runner = PostFireAssessment(gee_key_json,
                                    geojson_path, "2024-09-01", "2024-11-08", 
                                    deliverables=[
                                        Deliverable.RGB_PRE_FIRE,
                                        Deliverable.RGB_POST_FIRE,
                                        Deliverable.NDVI_PRE_FIRE,
                                        Deliverable.NDVI_POST_FIRE,
                                        Deliverable.RBR,
                                    ], 
                                    track_timings=True)

        # Run the analysis
        result = runner.run_analysis()

        # Print fire severity
        for row in result["area_by_severity"]:
            logger.info(
                f"{row['severity_name']}({row['severity']}): {row['ha']:.2f} ha ({row['percent']:.2f}%) -> {row['color']}"
            )

        # Save each deliverable to local files
        for key, item in result["images"].items():
            with open(item["filename"], "wb") as f:
                f.write(item["data"])
            logger.info(f"Saved file: {item['filename']}")

        # Print processing time metrics
        timings = result.get("timings", {})
        logger.info("Stats:")
        for key, value in timings.items():
            logger.info(f" → {key}: {value:.2f} sec")

        logger.info("Client ends")

    except Exception as e:
        logger.exception("Unexpected error during processing")

# Entry point
if __name__ == "__main__":
    main()
