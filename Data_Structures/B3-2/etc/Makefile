#make demo, test, clean
.PHONY: demo test clean

demo:
	python3 demo_script.py > mini_git_test.txt
	@echo "Saved to mini_git_test.txt"

test:
	python3 -m unittest test_graph -v

clean:
	rm -f mini_git_test.txt
	rm -rf __pycache__
