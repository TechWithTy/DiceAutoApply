import csv
from unittest.mock import MagicMock
from app.dice.utils.apply import write_job_titles_to_file

if __name__ == "__main__":
    from pathlib import Path
    tmp_path = Path("test_output")
    tmp_path.mkdir(exist_ok=True)

    # Setup dummy page
    dummy_page = MagicMock()
    dummy_page.context.new_page.return_value = dummy_page
    dummy_page.evaluate.return_value = "Test Job Title"
    dummy_page.wait_for_selector.return_value = True
    dummy_page.wait_for_load_state.return_value = None
    dummy_page.goto.return_value = None
    dummy_page.close.return_value = None

    # Patch evaluate_and_apply to simulate success/failure
    from app.dice.utils.apply import evaluate_and_apply
    evaluate_and_apply = MagicMock(side_effect=[True, False])

    job_ids = ["jobid1", "jobid2"]
    url = "https://www.dice.com/jobs?q=Test&location=Remote"
    csv_file = tmp_path / "job_titles.csv"

    # Run with explicit csv_file argument
    applied, failed, failed_jobs = write_job_titles_to_file(dummy_page, job_ids, url, str(csv_file))

    print(f"Applied: {applied}")
    print(f"Failed: {failed}")
    print(f"Failed Jobs: {failed_jobs}")
    print(f"CSV Output ({csv_file}):")
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(row)
