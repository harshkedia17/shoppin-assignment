#!/usr/bin/env python3
"""
Shopify Size Chart Extractor CLI
"""
import asyncio
import argparse
import logging
import sys
from typing import List
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.service import SizeChartExtractorService
from src.models.size_chart import ExtractionConfig

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract size charts from Shopify stores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s westside.com freakins.com
  %(prog)s westside.com --output results.json --max-products 50
  %(prog)s -f stores.txt --concurrent 3 --rate-limit 2.0
        """
    )

    parser.add_argument(
        'stores',
        nargs='*',
        help='Store URLs to extract (e.g., westside.com)'
    )

    parser.add_argument(
        '-f', '--file',
        help='File containing store URLs (one per line)'
    )

    parser.add_argument(
        '-o', '--output',
        default='output.json',
        help='Output JSON file (default: output.json)'
    )

    parser.add_argument(
        '--max-products',
        type=int,
        default=100,
        help='Maximum products per store (default: 100)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Seconds between requests (default: 1.0)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )

    parser.add_argument(
        '--concurrent',
        type=int,
        default=5,
        help='Maximum concurrent requests (default: 5)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    return parser.parse_args()


def load_stores_from_file(filepath: str) -> List[str]:
    """Load store URLs from file."""
    stores = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    stores.append(line)
    except Exception as e:
        console.print(f"[red]Error reading file {filepath}: {e}[/red]")
        sys.exit(1)
    return stores


def print_results_summary(results):
    """Print a summary table of extraction results."""
    table = Table(title="Extraction Results Summary")
    table.add_column("Store", style="cyan")
    table.add_column("Products Found", justify="right", style="green")
    table.add_column("With Size Charts", justify="right", style="green")
    table.add_column("Errors", justify="right", style="red")

    total_products = 0
    total_errors = 0

    for result in results:
        products_count = len(result.products)
        errors_count = len(result.errors)
        total_products += products_count
        total_errors += errors_count

        table.add_row(
            result.store_name,
            str(products_count),
            str(products_count),  # All products have size charts
            str(errors_count) if errors_count > 0 else "-"
        )

    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total_products}[/bold]",
        f"[bold]{total_products}[/bold]",
        f"[bold]{total_errors}[/bold]" if total_errors > 0 else "-"
    )

    console.print(table)


async def main_async():
    """Main async function."""
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    stores = args.stores
    if args.file:
        stores.extend(load_stores_from_file(args.file))

    if not stores:
        console.print("[red]Error: No stores specified[/red]")
        console.print("Use -h for help")
        sys.exit(1)

    stores = list(dict.fromkeys(stores))

    console.print(f"[cyan]Extracting size charts from {len(stores)} stores...[/cyan]")

    config = ExtractionConfig(
        max_products_per_store=args.max_products,
        rate_limit_delay=args.rate_limit,
        timeout=args.timeout,
        concurrent_requests=args.concurrent
    )

    service = SizeChartExtractorService(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Extracting size charts...", total=None)

        try:
            results = await service.run(stores, args.output)
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[red]Extraction failed: {e}[/red]")
            if args.debug:
                console.print_exception()
            sys.exit(1)

    console.print(f"\n[green]✓ Results saved to {args.output}[/green]\n")
    print_results_summary(results)


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Extraction cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
