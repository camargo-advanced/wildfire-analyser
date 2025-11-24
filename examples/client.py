# client.py

import logging
import os

from wildfire_analyser import PostFireAssessment

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    try:
        geojson_path = os.path.join("polygons", "eejatai.geojson")

        runner = PostFireAssessment(geojson_path, "2024-09-01", "2024-11-08")
        result = runner.run_analysis()

        # Exportar mosaicos com bandas adicionais
        #runner.save_mosaic_local(result["before"]["mosaic"], "before_mosaic_with_indices.tif", scale=10)
        #runner.save_mosaic_local(result["after"]["mosaic"], "after_mosaic_with_indices.tif", scale=10)
        runner.save_mosaic_local(result["rbr"], "RBR.tif", scale=10)

        logger.info("NDVI, NBR and RBR generated sucessfully")
    except Exception as e:
        logger.exception("Unexpected error during processing")

# Run code
main()
