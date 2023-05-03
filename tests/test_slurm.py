# coding: utf-8
# Copyright (c) Jan Janssen

import os
import pandas
import unittest
import getpass
from pysqa import QueueAdapter

__author__ = "Jan Janssen"
__copyright__ = "Copyright 2019, Jan Janssen"
__version__ = "0.0.1"
__maintainer__ = "Jan Janssen"
__email__ = "janssen@mpie.de"
__status__ = "production"
__date__ = "Feb 9, 2019"


class TestRunmode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = os.path.dirname(os.path.abspath(__file__))
        cls.slurm = QueueAdapter(directory=os.path.join(cls.path, "config/slurm"))

    def test_config(self):
        self.assertEqual(self.slurm.config["queue_type"], "SLURM")
        self.assertEqual(self.slurm.config["queue_primary"], "slurm")

    def test_list_clusters(self):
        self.assertEqual(self.slurm.list_clusters(), ['default'])

    def test_ssh_delete_file_on_remote(self):
        self.assertEqual(self.slurm.ssh_delete_file_on_remote, True)

    def test_interfaces(self):
        self.assertEqual(
            self.slurm._adapter._commands.submit_job_command, ["sbatch", "--parsable"]
        )
        self.assertEqual(self.slurm._adapter._commands.delete_job_command, ["scancel"])
        self.assertEqual(
            self.slurm._adapter._commands.get_queue_status_command,
            ["squeue", "--format", "%A|%u|%t|%.15j|%Z", "--noheader"],
        )

    def test__list_command_to_be_executed(self):
        with self.subTest("slurm"):
            self.assertEqual(
                self.slurm._adapter._list_command_to_be_executed(None, "here"),
                ["sbatch", "--parsable", "here"],
            )
        with self.subTest("slurm with one dependency"):
            self.assertEqual(
                self.slurm._adapter._list_command_to_be_executed(["2"], "here"),
                ["sbatch", "--parsable", "--dependency=afterok:2", "here"],
            )
        with self.subTest("slurm with two dependencies"):
            self.assertEqual(
                self.slurm._adapter._list_command_to_be_executed(["2", "34"], "here"),
                ["sbatch", "--parsable", "--dependency=afterok:2,34", "here"],
            )

    def test_convert_queue_status_slurm(self):
        with open(os.path.join(self.path, "config/slurm", "squeue_output"), "r") as f:
            content = f.read()
        df_verify = pandas.DataFrame(
            {
                "jobid": [5322019, 5322016, 5322017, 5322018, 5322013],
                "user": ["janj", "janj", "janj", "janj", "janj"],
                "jobname": ["pi_19576488", "pi_19576485", "pi_19576486", "pi_19576487", "pi_19576482"],
                "status": ["running", "running", "running", "running", "running"],
                "working_directory": [
                    "/cmmc/u/janj/pyiron/projects/2023/2023-04-19-dft-test/job_1",
                    "/cmmc/u/janj/pyiron/projects/2023/2023-04-19-dft-test/job_2",
                    "/cmmc/u/janj/pyiron/projects/2023/2023-04-19-dft-test/job_3",
                    "/cmmc/u/janj/pyiron/projects/2023/2023-04-19-dft-test/job_4",
                    "/cmmc/u/janj/pyiron/projects/2023/2023-04-19-dft-test/job_5",
                ]
            }
        )
        self.assertTrue(
            df_verify.equals(
                self.slurm._adapter._commands.convert_queue_status(
                    queue_status_output=content
                )
            )
        )

    def test_get_user(self):
        self.assertEqual(self.slurm._adapter._get_user(), getpass.getuser())

    def test_queue_view(self):
        self.assertIsInstance(self.slurm.queue_view, pandas.DataFrame)

    def test_submit_job_empty_working_directory(self):
        with self.assertRaises(ValueError):
            self.slurm.submit_job(working_directory=" ")

    def test_write_queue(self):
        with self.assertRaises(ValueError):
            self.slurm._adapter._write_queue_script(
                queue=None,
                job_name=None,
                working_directory=None,
                cores=None,
                memory_max=None,
                run_time_max=None,
                command=None
            )
        self.slurm._adapter._write_queue_script(
            queue="slurm",
            job_name=None,
            working_directory=None,
            cores=None,
            memory_max=None,
            run_time_max=None,
            command="echo \"hello\""
        )
        with open("run_queue.sh", "r") as f:
            content = f.read()
        output = """\
#!/bin/bash
#SBATCH --output=time.out
#SBATCH --job-name=None
#SBATCH --chdir=.
#SBATCH --get-user-env=L
#SBATCH --partition=slurm
#SBATCH --time=4320
#SBATCH --cpus-per-task=10

echo \"hello\""""
        self.assertEqual(content, output)
        os.remove("run_queue.sh")

    def test_write_queue_extra_keywords(self):
        self.slurm._adapter._write_queue_script(
            queue="slurm_extra",
            job_name=None,
            working_directory=None,
            cores=None,
            memory_max=None,
            run_time_max=None,
            command="echo \"hello\"",
            account="123456"
        )
        with open("run_queue.sh", "r") as f:
            content = f.read()
        output = """\
#!/bin/bash
#SBATCH --output=time.out
#SBATCH --job-name=None
#SBATCH --chdir=.
#SBATCH --get-user-env=L
#SBATCH --partition=slurm
#SBATCH --account=123456
#SBATCH --time=4320
#SBATCH --cpus-per-task=10

echo \"hello\""""
        self.assertEqual(content, output)
        os.remove("run_queue.sh")