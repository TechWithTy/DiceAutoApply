# Document Builder (Resumes & Cover Letters)

A Python-based ATS-friendly pipeline for generating resumes and cover letters using ReportLab. 

## Structure

```
backend/resume_builder/
├── generator.py           # The CLI entry point
├── templates/
│   ├── standard.py        # ATS 1-page resume template
│   └── cover_letter.py    # Matching cover letter template
├── data/
│   ├── base.json          # Master JSON copy for resume
│   └── cover_letter_base.json # Master JSON copy for cover letters
└── output/
    └── .pdf files         # The generated PDF documents
```

## How to generate a new document
1. Duplicate `data/base.json` or `data/cover_letter_base.json` depending on what you're making.
2. Tweak the duplicate's contents to match the job.
3. Run the generation script:

```bash
# Generate Resume (defaults to standard template)
python generator.py data/front_end_dev_google.json output/front_end_dev_google_resume.pdf

# Generate Cover Letter
python generator.py data/front_end_dev_google_cl.json output/front_end_dev_google_cover_letter.pdf --template cover_letter
```
