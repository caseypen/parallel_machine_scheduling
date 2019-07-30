all:
	# make dynamic library for cython package
	python setup.py build_ext --inplace
test:
	python -m -cProfile -s tottime solver_test.py
clean:
	rm ./bin/*.so jsp_bbs.cpp