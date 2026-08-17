# Research data

Document every dataset used by the project here. For each source, record:

- the source or persistent identifier;
- the date and method of retrieval;
- the licence and any access restrictions;
- a checksum for the original file; and
- every transformation applied before analysis.

A useful local structure is:

```text
data/
├── raw/        # immutable source data
├── interim/    # intermediate transformations
└── processed/  # analysis-ready datasets
```

The three directories above are ignored by Git by default. Use an appropriate
data repository, object store, DVC, or Git LFS when collaborators need access
to large files. Never commit credentials, confidential records, or data that
cannot legally be redistributed.
