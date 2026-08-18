.PHONY: demo test clean

demo:
	python3 demo_script.py > mini_git_demo_output.txt
	@echo "Saved to mini_git_demo_output.txt"

test:
	python3 -m unittest test_graph -v

clean:
	rm -f mini_git_demo_output.txt
	rm -rf __pycache__
