import os
import click
import re
import shutil
import subprocess
import sys
import difflib
from zipfile import ZipFile

# === Utility functions ===

def _run_test_case(entrypoint, input_path, output_path, timeout=30):
    """Run a single test case: execute `entrypoint` with stdin from input_path.

    Returns a tuple: (status, stdout, stderr, diff_lines)
    status is one of: 'PASS', 'FAIL', 'TIMEOUT', 'NO EXPECTED OUTPUT'
    diff_lines is a list of unified-diff lines when status == 'FAIL', else None.
    """
    try:
        with open(input_path, 'rb') as stdin_f:
            proc = subprocess.run([sys.executable, entrypoint], stdin=stdin_f,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ("TIMEOUT", "", "", None)

    stdout = proc.stdout.decode('utf-8', errors='replace').replace('\r\n', '\n')
    stderr = proc.stderr.decode('utf-8', errors='replace')

    expected = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8', errors='replace') as ef:
            expected = ef.read().replace('\r\n', '\n')

    def norm(s):
        if s is None:
            return None
        return '\n'.join([line.rstrip() for line in s.split('\n')]).rstrip()

    out_norm = norm(stdout)
    exp_norm = norm(expected) if expected is not None else None

    if expected is None:
        return ("NO EXPECTED OUTPUT", stdout, stderr, None)
    if out_norm == exp_norm:
        return ("PASS", stdout, stderr, None)

    diff_lines = list(difflib.unified_diff((exp_norm or '').split('\n'), out_norm.split('\n'), fromfile='expected', tofile='actual', lineterm=''))
    return ("FAIL", stdout, stderr, diff_lines)


# === CLI commands ===

@click.group()
def cli():
    pass


@cli.command()
@click.argument('skeleton_path', required=True)
@click.option('--out', '-o', help="Output directory", default=None, type=click.Path())
@click.option('--recursive-backup', default=True, is_flag=True, help="Enable recursive backup of existing files")
def init(skeleton_path, out, recursive_backup):
    if out is None:
        match = re.search(r'lab\d+', skeleton_path)
        if match:
            out = f"./{match.group(0)}"
        else:
            out = f"./{skeleton_path.rsplit('.', 1)[0]}"

    # Check if output directory exists, prompt for confirmation
    if os.path.exists(out):
        click.confirm(
            f"The directory {out} already exists. Do you want to overwrite it?", abort=True)
        shutil.rmtree(out)

    tmp_dir = os.path.join(out, "../.zincon_tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    with ZipFile(skeleton_path, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    files = os.listdir(tmp_dir)

    # if the zip contains a single top-level directory, move its contents up
    if len(files) == 1 and os.path.isdir(os.path.join(tmp_dir, files[0])):
        tld = os.path.join(tmp_dir, files[0])
        for item in os.listdir(tld):
            os.rename(
                os.path.join(tld, item),
                os.path.join(tmp_dir, item)
            )

    # backup existing files
    skeleton_files = os.listdir(tmp_dir)
    backup_dir = os.path.join(tmp_dir, "backup")
    if recursive_backup:
        shutil.copytree(tmp_dir, backup_dir, dirs_exist_ok=True)
    else:
        for file in skeleton_files:
            src = os.path.join(tmp_dir, file)
            shutil.copyfile(src, os.path.join(backup_dir, file))

    # create .zincon-submit file
    zincon_submit_path = os.path.join(tmp_dir, '.zincon-submit')
    with open(zincon_submit_path, 'w') as f:
        for file in skeleton_files:
            if (os.path.isfile(os.path.join(tmp_dir, file))):
                f.write(f"{file}\n")
        f.write("# Add additional files to submit here\n")

    # clean up temporary directory
    os.rename(tmp_dir, out)
    print(f"Initialized skeleton at {out}")


@cli.command()
@click.argument('path', required=True, type=click.Path(exists=True))
@click.option('--out', '-o', help="Output zip file path", default=None, type=click.Path())
def pack(path, out):
    # Check if output directory exists, prompt for confirmation
    if out is None:
        out = os.path.join(path, 'submission.zip')
    if os.path.exists(out):
        click.confirm(
            f"The file {out} already exists. Do you want to overwrite it?", abort=True)
        os.path.remove(out)

    # Read .zincon-submit file
    zincon_submit_path = os.path.join(path, '.zincon-submit')
    files_to_pack = []
    if os.path.exists(zincon_submit_path):
        with open(zincon_submit_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    files_to_pack.append(line)
        with ZipFile(out, 'w') as zipf:
            for file in files_to_pack:
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=file)
                else:
                    click.echo(
                        f"Warning: {file} listed in .zincon-submit not found in {path}. Skipping.")
    else:
        click.echo(
            f"No .zincon-submit file found in {path}. Packing all files.")
        shutil.make_archive(out, 'zip', path)


@cli.command()
@click.argument('path', required=True, type=click.Path(exists=True))
@click.argument('entrypoint', required=True, type=click.Path())
@click.argument('testcases_dir', default="testcases", type=click.Path())
@click.option('--ifmt', help="Input format", default="input{}.txt")
@click.option('--ofmt', help="Output format", default="output{}.txt")
@click.option('--timeout', help="Timeout per test case in seconds", default=30, type=int)
def test(path, entrypoint, testcases_dir, ifmt, ofmt, timeout):
    # Verify testcases directory and try absolute path if failed to join
    joined_testdir = os.path.join(path, testcases_dir)
    if os.path.exists(joined_testdir):
        testcases_dir = joined_testdir
    elif os.path.exists(testcases_dir):
        testcases_dir = testcases_dir
    else:
        click.echo(f"Testcases directory {testcases_dir} does not exist.")
        return

    # Verify entrypoint file
    entrypoint_path = os.path.join(path, entrypoint)
    if os.path.exists(entrypoint_path):
        entrypoint = entrypoint_path
    elif os.path.exists(entrypoint):
        entrypoint = entrypoint
    else:
        click.echo(f"Entrypoint file {entrypoint} does not exist.")
        return

    # Iterate through each input file, find corresponding output file and process
    results = []
    for filename in os.listdir(testcases_dir):
        if re.match(ifmt.format(r'(\d+)'), filename):
            testcase_num = re.findall(r'\d+', filename)[0]
            input_path = os.path.join(testcases_dir, filename)
            output_path = os.path.join(
                testcases_dir, ofmt.format(testcase_num))
            click.echo(f"Running test case {testcase_num}...")

            # run test case
            status, stdout, stderr, diff_lines = _run_test_case(entrypoint, input_path, output_path, timeout=timeout)

            if status == "TIMEOUT":
                click.echo(f"Test {testcase_num}: TIMEOUT")
                results.append((testcase_num, "TIMEOUT", ""))
                continue

            if status == "NO EXPECTED OUTPUT":
                click.echo(f"Test {testcase_num}: (no expected output) -- script stdout:\n{stdout}")
                results.append((testcase_num, "NO EXPECTED OUTPUT", stdout))
                continue

            if status == "PASS":
                click.echo(f"Test {testcase_num}: PASS")
                results.append((testcase_num, "PASS", stdout))
                continue

            # otherwise it's a FAIL
            click.echo(f"Test {testcase_num}: FAIL")
            results.append((testcase_num, "FAIL", stdout))
            else:
                click.echo(f"Test {testcase_num}: FAIL")
                results.append((testcase_num, "FAIL", stdout))
                # show a small unified diff
                diff = difflib.unified_diff(
                    (exp_norm or '').split('\n'),
                    out_norm.split('\n'),
                    fromfile='expected',
                    tofile='actual',
                    lineterm=''
                )
                for line in diff:
            if diff_lines:
                for line in diff_lines:
                    click.echo(line)
            if stderr:
                click.echo('\n--- stderr ---')
                click.echo(stderr)
            click.echo('\n\n--- end of test case ---\n\n')

    # Final statistics
    print("\nSummary of test results:")
    passed = 0
    total = 0
    for testcase_num, status, _ in results:
        print(f"Test {testcase_num}: {status}")
        if status == "PASS":
            passed += 1
        total += 1
    print(f"Passed {passed} out of {total} tests.")


if __name__ == '__main__':
    cli()
