import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='ansi-string',
    author='James Smith',
    author_email='jmsmith86@gmail.com',
    description='ANSI String Formatter in Python for CLI Color and Style Formatting',
    keywords='ANSI, string',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Tails86/ansi-string',
    project_urls={
        'Documentation': 'https://github.com/Tails86/ansi-string',
        'Bug Reports': 'https://github.com/Tails86/ansi-string/issues',
        'Source Code': 'https://github.com/Tails86/ansi-string'
    },
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    extras_require={
        'dev': ['check-manifest']
    }
)