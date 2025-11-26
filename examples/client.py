# client.py
import logging
import os

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
        # Path to the GeoJSON polygon used as the Region of Interest (ROI)
        geojson_path = os.path.join("polygons", "eejatai.geojson")

        # Initialize the wildfire assessment processor with date range
        runner = PostFireAssessment(geojson_path, "2024-09-01", "2024-11-08", 
                                    deliverables=[
                                        Deliverable.RGB_PRE_FIRE,
                                        #Deliverable.RGB_POST_FIRE,
                                        #Deliverable.NDVI_PRE_FIRE,
                                        #Deliverable.NDVI_POST_FIRE,
                                        #Deliverable.RBR,
                                    ])

        # Run the analysis, which returns a dictionary with binary GeoTIFFs
        result = runner.run_analysis()

        # Print fire severity
        for sev_value, area in result["area_by_severity"].items():
            sev = FireSeverity(sev_value)
            logger.info(f"{sev.label}: {area:.2f} ha")

        # Save each deliverable to local files
        for key, item in result["images"].items():
            with open(item["filename"], "wb") as f:
                f.write(item["data"])
            logger.info(f"Saved file: {item['filename']}")

        # Timings
        timings = result.get("timings", {})
        logger.info("Stats:")
        for key, value in timings.items():
            logger.info(f" → {key}: {value:.2f} sec")

        logger.info("Client ends")

    except Exception as e:
        logger.exception("Unexpected error during processing")

# Entry point
main()
