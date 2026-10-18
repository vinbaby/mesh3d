VIN 3D Studio v0.10.1 — Extend Existing Rig + Fast Preview

SUA LOI TREN FILE DA CO SKIN
- Auto Rig khong tao them skeleton trung len file da co skin. Bam Auto Rig tren file da rig se hien huong dan ro rang thay vi popup "Auto Rig Failed" chung chung.
- Rig Studio > Manual Rig Mode nay co the vao che do "Extend Existing Rig" cho GLB co dung 1 skin, khong co animation clips va khong co morph targets.
- Skeleton hien co duoc hien thi lam tham chieu, khong the xoa/doi vi tri trong luong mo rong. Boi vay bind pose, joint indices va JOINTS_0 / WEIGHTS_0 hien tai duoc giu nguyen.
- Khi bam Hands / Feet / Face, VIN tim bone cha hien co theo cac ten alias (vi du Hand_L co the map den LeftHand) va chi them cac helper joint con thieu, khong tao skeleton thu hai.
- Nut xuat doi thanh "Extend Existing Rig + Save Copy" va tao file *_extended_rig.glb moi. File goc khong bi ghi de.
- Bone phu moi duoc them vao skin nhung chua co weight influence. Sau khi xuat, mo Weight Paint va gan weight cho cac bone phu truoc khi mong doi chung lam bien dang mesh. Cac mesh rieng khong nam trong skin hien co van giu nguyen trang thai.
- Extension hien tai bao ve file: tu choi GLB co animation, morph targets, nhieu skin, nhieu mesh node dung skin hoac ten bone cha khong xac dinh ro rang.

CAI DAT
1. Dong VIN 3D Studio.
2. Giai nen toan bo ZIP vao thu muc co run_windows.bat.
3. Chay UPDATE_TO_V0.10.1.bat.
4. Chi tiep tuc neu hien UPDATE SUCCESS. Neu test fail, updater thu rollback va giu ban sao luu.

CACH DUNG VOI FILE DA RIG
1. Import GLB da co skin va mo Rig Studio > Manual Rig.
2. Bam Enable Manual Rig Mode; neu file du dieu kien, nut chuyen thanh Manual Rig · Extend Existing.
3. Chon trang Hands / Feet / Face va bam joint muon them. VIN dung bone hien co lam parent neu tim duoc, con joint moi hien thanh knot de keo can chinh.
4. Bam Extend Existing Rig + Save Copy.
5. Dung Weight Paint de them influence cho bone phu moi. Weight va cac joint cu duoc giu nguyen.

GIOI HAN
- Da thu tren cucaosu.glb (1 skin, 8 joint, 5 mesh node tong cong; 1 node dung skin): them 2 helper joint vao ban sao thanh cong, giu nguyen JOINTS_0 / WEIGHTS_0 va file goc.
- Regression tests: test extension GLB, bao toan weight, parenting va UI contract se duoc chay boi updater tren may Windows.
- Chua kiem tra mo file extended trong Blender tren GPU Windows cua nguoi dung. Bone phu khong co weights tu dong; can Weight Paint.
