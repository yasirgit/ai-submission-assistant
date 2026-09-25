.PHONY: eval

eval:
	cd backend && uv run python -m app.evaluation
