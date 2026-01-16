import logging
import os
from dotenv import load_dotenv
import argparse
from pathlib import Path

from wildfire_analyser.fire_assessment.post_fire_assessment import PostFireAssessment
from wildfire_analyser.fire_assessment.deliverables import Deliverable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        load_dotenv()

        gee_key_json = os.getenv("GEE_PRIVATE_KEY_JSON")
        if not gee_key_json:
            raise RuntimeError("GEE_PRIVATE_KEY_JSON not set")

        gcs_bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not gcs_bucket_name:
            raise RuntimeError("GCS_BUCKET_NAME not set")

        parser = argparse.ArgumentParser(
            description="Post-fire assessment using Google Earth Engine"
        )

        parser.add_argument(
            "--roi",
            required=True,
            help="Path to ROI GeoJSON file"
        )

        parser.add_argument(
            "--start-date",
            required=True,
            help="Start date (pre-fire) in YYYY-MM-DD format"
        )

        parser.add_argument(
            "--end-date",
            required=True,
            help="End date (post-fire) in YYYY-MM-DD format"
        )

        parser.add_argument(
            "--deliverables",
            nargs="+",
            help=(
                "List of deliverables to generate. "
                "Example: --deliverables RGB_PRE_FIRE DNBR"
            ),
        )

        parser.add_argument(
            "--deliverables-all",
            action="store_true",
            help="Generate all available deliverables"
        )

        parser.add_argument(
            "--days-before-after",
            type=int,
            default=30,
            help="Number of days before and after the event date to search imagery (default: 30)"
        )

        args = parser.parse_args()

        DEFAULT_DELIVERABLES = [
            Deliverable.RGB_PRE_FIRE,
            Deliverable.RGB_POST_FIRE,
            Deliverable.NBR_PRE_FIRE,
            Deliverable.NBR_POST_FIRE,
            Deliverable.DNBR,
            Deliverable.RBR,
            Deliverable.BURN_SEVERITY_MAP,
            Deliverable.RGB_PRE_FIRE_VISUAL,
            Deliverable.RGB_POST_FIRE_VISUAL,
            Deliverable.DNBR_VISUAL,
            Deliverable.BURN_SEVERITY_VISUAL,
            Deliverable.BURNED_AREA_STATISTICS,
        ]

        if args.deliverables_all and args.deliverables:
            raise ValueError(
                "Use either --deliverables-all or --deliverables, not both."
            )

        if args.deliverables_all:
            deliverables = list(Deliverable)

        elif args.deliverables:
            try:
                deliverables = [Deliverable[name] for name in args.deliverables]
            except KeyError as e:
                valid = ", ".join(d.name for d in Deliverable)
                raise ValueError(
                    f"Invalid deliverable '{e.args[0]}'. "
                    f"Valid options are: {valid}"
                )

        else:
            deliverables = DEFAULT_DELIVERABLES

        geojson_path = Path(args.roi).expanduser().resolve()
        if not geojson_path.exists():
            raise FileNotFoundError(f"GeoJSON not found: {geojson_path}")

        runner = PostFireAssessment(
            gee_key_json=gee_key_json,
            geojson_path=str(geojson_path),
            start_date=args.start_date,
            end_date=args.end_date,
            days_before_after=args.days_before_after,
            deliverables=deliverables, 
            gcs_bucket=gcs_bucket_name,
        )

        result = runner.run()

        logger.info("Scientific outputs:")
        for name, item in result["scientific"].items():
            logger.info("  %s -> %s", name, item["url"])

        logger.info("Visual outputs:")
        for name, item in result["visual"].items():
            logger.info("  %s -> %s", name, item["url"])

        logger.info("Statistics:")
        for cls, values in result["statistics"].items():
            logger.info(
                f"{cls:<20} | Area (ha): {values['area_ha']:8.2f} | "
                f"Ratio (%): {values['ratio_percent']:6.2f}"
            )

        logger.info("Image provenance (ordered by cloud cover):")

        for phase in ("pre_fire", "post_fire"):
            images = result["provenance"].get(phase, {}).get("images", [])

            logger.info("  %s (%d images)", phase.replace("_", " ").title(), len(images))

            for img in images:
                logger.info(
                    "    %s | %s | clouds: %5.2f%%",
                    img["date"],
                    img["id"],
                    img["cloud_percent"],
                )
    
    except ValueError as e:
        logger.error(str(e))
        raise SystemExit(2)

    except FileNotFoundError as e:
        logger.error(str(e))
        raise SystemExit(2)

    except RuntimeError as e:
        logger.error(str(e))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
