"""Tests for SingleInstanceLock — cross-platform single-instance enforcement."""

import sys

import pytest

from src.main import SingleInstanceLock


class TestSingleInstanceLockPosix:
    """Tests for the POSIX (macOS/Linux) flock path."""

    @pytest.fixture(autouse=True)
    def skip_on_windows(self):
        if sys.platform == "win32":
            pytest.skip("POSIX lock tests do not run on Windows")

    def test_first_acquire_succeeds(self, tmp_path):
        lock = SingleInstanceLock(lock_file=tmp_path / "test.lock")
        assert lock.acquire() is True
        lock.release()

    def test_second_acquire_fails_while_first_held(self, tmp_path):
        lock_file = tmp_path / "test.lock"
        lock1 = SingleInstanceLock(lock_file=lock_file)
        lock2 = SingleInstanceLock(lock_file=lock_file)

        assert lock1.acquire() is True
        assert lock2.acquire() is False
        lock1.release()

    def test_acquire_succeeds_after_release(self, tmp_path):
        lock_file = tmp_path / "test.lock"
        lock1 = SingleInstanceLock(lock_file=lock_file)
        lock2 = SingleInstanceLock(lock_file=lock_file)

        lock1.acquire()
        lock1.release()
        assert lock2.acquire() is True
        lock2.release()

    def test_release_is_idempotent(self, tmp_path):
        lock = SingleInstanceLock(lock_file=tmp_path / "test.lock")
        lock.acquire()
        lock.release()
        lock.release()  # should not raise


class TestSingleInstanceLockWindows:
    """Tests for the Windows named-mutex path."""

    @pytest.fixture(autouse=True)
    def skip_on_non_windows(self):
        if sys.platform != "win32":
            pytest.skip("Windows mutex tests only run on Windows")

    def test_first_acquire_succeeds(self):
        lock = SingleInstanceLock(mutex_name="TestApp_SingleInstance_1")
        assert lock.acquire() is True
        lock.release()

    def test_second_acquire_fails_while_first_held(self):
        lock1 = SingleInstanceLock(mutex_name="TestApp_SingleInstance_2")
        lock2 = SingleInstanceLock(mutex_name="TestApp_SingleInstance_2")

        assert lock1.acquire() is True
        assert lock2.acquire() is False
        lock1.release()

    def test_acquire_succeeds_after_release(self):
        lock1 = SingleInstanceLock(mutex_name="TestApp_SingleInstance_3")
        lock2 = SingleInstanceLock(mutex_name="TestApp_SingleInstance_3")

        lock1.acquire()
        lock1.release()
        assert lock2.acquire() is True
        lock2.release()

    def test_release_is_idempotent(self):
        lock = SingleInstanceLock(mutex_name="TestApp_SingleInstance_4")
        lock.acquire()
        lock.release()
        lock.release()  # should not raise
