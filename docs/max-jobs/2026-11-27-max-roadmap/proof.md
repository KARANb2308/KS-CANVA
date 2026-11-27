C1 ผ่าน — test_max_lite TestRoadmap.test_dir_m_creates_map + test_dir_twice_and_s (53/53 OK)
C2 ผ่าน — TestRecord.test_gate_build: ledger ด่าน: สร้าง, แผนที่บรรทัดเดียว, stdout ด่าน: [j1] (53/53 OK)
C5 ผ่าน — TestRoadmap.test_todo_next_wait_done + test_todo_cap + test_done_not_found_and_ambiguous (53/53 OK)
C9 ผ่าน — TestRecord.test_clean_secrets + test_whitelist + test_no_over_cut + test_big_file_truncated (53/53 OK)
C11 ผ่าน — TestRoadmap.test_real_git_merge_union + test_conflict_markers_and_dupes (53/53 OK)
C17 ผ่าน — TestRecord.test_gate_plan + test_gate_plan_missing (53/53 OK)
C3 ผ่าน — TestCloseRecord.test_close_ok + test_eleven_jobs_cap (76/76 OK)
C4 ผ่าน — TestCloseRecord.test_abandon_with_spec + test_abandon_without_spec (76/76 OK)
C8 ผ่าน — TestRecord.test_gate_build + TestCloseRecord.test_close_ok record.md ทั้ง gate และ close (76/76 OK)
C9 ผ่าน — เพิ่ม TestRecord test_clean_prefixed_and_json_keys, test_clean_basic_auth_and_url, test_clean_paths_unit, test_clean_home_unit (76/76 OK)
C10 ผ่าน — TestCloseRecord.test_fail_after_2/3/4 + test_close_refused_writes_nothing + test_turns (76/76 OK)
C6 ผ่าน — TestResume.test_status_recoverable_then_resume + test_status_lost_job + test_status_next_top3 + test_status_repairs_half_closed (94/94 OK)
C7 ผ่าน — TestResume.test_status_recoverable_then_resume + test_resume_never_overwrites + test_resume_errors (94/94 OK)
C12 ผ่าน — TestRecheck.test_recheck_fallbacks + TestResume.test_backfill* (121/121 OK)
C13 ผ่าน — TestRecheck.test_recheck_prints พิมพ์ทุก C-id + ช่วง + ไฟล์ ไม่เขียนไฟล์ (121/121 OK)
C14 ผ่าน — TestRecheck.test_sum + test_sum_incomplete_writes_nothing + test_last_line_wins (121/121 OK)
C15 ผ่าน — TestRecheck.test_repeat งานเปิดและงานปิดแล้ว (121/121 OK)
C16 ผ่าน — TestStats.test_stats_exact + test_stats_empty + test_stats_broken_records (121/121 OK)
C18 ผ่าน — SKILL.md description มี "ทำต่อ" "ตรวจซ้ำ" "แผนที่งาน"; SKILL.md บรรทัด 94 "ทำต่อ"=status→resume; ml.md M โชว์แผนแล้วทำต่อ / L,XL gate plan แล้วรอ "ลุย"; ลองจริง ข: transcript มี status แล้ว resume t-resume
C19 ผ่าน — references/roadmap.md + recheck.md มีจริง; คำสั่ง dir/gate/status/resume/close/recheck/--sum/todo รันจริงในรอบ ก ข ค ผ่านหมด (exit 0)
C20 ผ่าน — test_max_lite.py 121/121 OK รันใหม่; SKILL.md 11609 + ml.md 11895 = 23504 bytes ≤ 23736
C21 ผ่าน — cmp 2 คู่ SAME; version 8.4.0 ทั้ง plugin.json และ marketplace.json; claude plugin validate . = Validation passed with warnings (README install line เตือนเท่านั้น)
C22 ผ่าน — docs/roadmap.md 14 บรรทัด (PR #1 รอผู้ใช้, dbp.co.th P1, max-upgrade เสร็จ, max-roadmap กำลังทำ), .gitattributes merge=union, docs/max-jobs/ มี max-upgrade (SPEC ledger preflight proof record) + max-roadmap, git check-ignore ไม่ ignore, recheck max-upgrade = 16 บรรทัด, check-worker-sync IN SYNC
C23 ผ่าน — ลองจริง ก: รอบ1 is_error=false turns=24 cost=0.81; record.md สถานะ ปิด, roadmap เสร็จล่าสุด [slugify]; หลัง rm -rf .max รอบ2 "ตรวจซ้ำ slugify" is_error=false turns=12 cost=0.84; recheck-2026-11-27.md C1-C8 ยังผ่านครบ, record.md มี ตรวจซ้ำ: 2026-11-27 ยังผ่าน 8. หมายเหตุ: MAX commit docs/ เองในรอบ 1 (ผู้ใช้สั่ง commit) จึงไม่ได้จด "ไม่ commit เอง"
C24 ผ่าน — ลองจริง ข: repo2 ก่อน record สถานะ กำลังทำ + ไม่มี .max; "ทำต่อ" is_error=false turns=25 cost=0.75; record.md สถานะ ปิด C-id 2, python3 -m unittest Ran 2 OK, ไม่มี [t-resume] ใต้ กำลังทำ, transcript มี status แล้ว resume t-resume. หมายเหตุ: ไฟล์ค้างไม่ commit และ record.md ไฟล์: มี __pycache__/*.pyc
C25 ผ่าน — ลองจริง ค: break sha f2876ea; รอบ3 "ตรวจซ้ำ slugify" is_error=false turns=14 cost=0.96; recheck มี C3 C5 C7 พังแล้ว — f2876ea "break"; roadmap ถัดไป (P1) แก้ slugify C3/C5/C7; git diff --stat f2876ea -- textutil.py ว่าง
C26 ผ่าน — grep /home/user|hunter2|APP_PASSWORD=...: ใน docs/max-jobs 3 บรรทัดทั้งหมดเป็นข้อความอธิบายใน SPEC ของงานนี้เอง (ledger ตัดสินยอมรับ) และ plugins/max-v8 มีเฉพาะค่าปลอม hunter2secret ใน test_max_lite.py; ไม่มี path เครื่อง/ความลับจริง; max-upgrade = 0
C27 ผ่าน — ลองจริง รอบ4 "ตรวจซ้ำละเอียด slugify" is_error=false turns=24 cost=1.71; มี hunt-2026-11-27.md (เจอบั๊ก C3/C5 + 5 ข้อรอง ลงถัดไป), transcript เรียก max-hunter และ code-review; ไม่แก้โค้ด (git diff f2876ea -- textutil.py ว่าง)
C16 ผ่าน — stats ของจริงใน repo ก พิมพ์ 6 บรรทัดตามรูป: งาน 1 (ปิด 1), แจ้งซ้ำ 0, C-id 8 ยังไม่ได้ตรวจ 0, เกินเพดาน 0, turn เฉลี่ย M 9, ตรวจซ้ำ 2 ครั้ง พังแล้ว 3
C13 ผ่าน — หลังรอบแก้ code-review: test_max_lite.py 136 เทส OK · claude plugin validate ผ่าน · reviewer PASS
