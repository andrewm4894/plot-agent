#!/usr/bin/env python3
import os
import glob
import papermill as pm
from pathlib import Path
import time
from statistics import mean
import logging
from datetime import datetime
import concurrent.futures
import argparse

def setup_logging():
    """
    Set up logging to both console and file.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    log_file = project_root / 'examples' / 'run_log.txt'
    
    # Create a logger
    logger = logging.getLogger('notebook_runner')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file, mode='w')
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(message)s')
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Add a separator for new run
    logger.info("\n" + "="*50)
    logger.info(f"New run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)
    logger.info("This script was run using 'make run-examples'")
    logger.info("To run locally, ensure you have the required dependencies installed")
    logger.info("and run: python scripts/run_examples.py")
    logger.info("="*50 + "\n")
    
    return logger

def run_notebook(notebook, logger):
    """
    Run a single notebook and return its execution time.
    """
    notebook_name = Path(notebook).name
    logger.info(f"Running notebook: {notebook_name}")
    start_time = time.time()
    try:
        pm.execute_notebook(
            notebook,
            notebook,  # Run in place by using the same path for input and output
            kernel_name='python3'
        )
        execution_time = time.time() - start_time
        logger.info(f"Successfully executed: {notebook_name}")
        logger.info(f"Execution time ({notebook_name}): {execution_time:.2f} seconds")
        return notebook_name, execution_time
    except Exception as e:
        logger.error(f"Error executing {notebook_name}: {str(e)}")
        raise

def run_examples(max_workers=1):
    """
    Run all example notebooks in parallel and track execution times.
    
    Args:
        max_workers (int): Maximum number of notebooks to run in parallel
    """
    logger = setup_logging()
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Path to examples directory
    examples_dir = project_root / 'examples'
    
    # Find all example notebooks
    example_notebooks = sorted(glob.glob(str(examples_dir / 'example_*.ipynb')))
    
    # Track execution times and notebook names
    execution_data = []  # List of tuples (notebook_name, execution_time)
    
    # Run notebooks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all notebooks for execution
        future_to_notebook = {
            executor.submit(run_notebook, notebook, logger): notebook 
            for notebook in example_notebooks
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_notebook):
            notebook = future_to_notebook[future]
            try:
                result = future.result()
                if result:
                    execution_data.append(result)
            except Exception as e:
                logger.error(f"Notebook {notebook} generated an exception: {str(e)}")
                raise
    
    # Print summary statistics
    if execution_data:
        execution_times = [time for _, time in execution_data]
        logger.info("\nExecution Summary:")
        logger.info(f"Total notebooks executed: {len(execution_data)}")
        logger.info(f"Total execution time: {sum(execution_times):.2f} seconds")
        logger.info(f"Average execution time: {mean(execution_times):.2f} seconds")
        
        # Find fastest and slowest notebooks
        fastest = min(execution_data, key=lambda x: x[1])
        slowest = max(execution_data, key=lambda x: x[1])
        logger.info(f"Fastest notebook: {fastest[0]} ({fastest[1]:.2f} seconds)")
        logger.info(f"Slowest notebook: {slowest[0]} ({slowest[1]:.2f} seconds)")
        
        # Add final separator
        logger.info("\n" + "="*50 + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run example notebooks in parallel')
    parser.add_argument('--max-workers', type=int, default=1,
                      help='Maximum number of notebooks to run in parallel (default: 1)')
    args = parser.parse_args()
    run_examples(max_workers=args.max_workers) 