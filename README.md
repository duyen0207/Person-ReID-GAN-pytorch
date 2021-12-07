# Person-reid-GAN-pytorch
Triển khai bằng Pytorch của bài báo ["Unlabeled Samples Generated by GAN Improve the Person Re-identification Baseline in vitro"(ICCV17)](http://openaccess.thecvf.com/content_ICCV_2017/papers/Zheng_Unlabeled_Samples_Generated_ICCV_2017_paper.pdf),code gốc tại [here](https://github.com/layumi/Person-reID_GAN)(matlab).

Tham khảo code mẫu từ https://github.com/qiaoguan/Person-reid-GAN-pytorch

## Chuẩn bị
- Python 2.7
- GPU 
- Numpy
- Pytorch
- Torchvision
- 
### Cài đặt
- Pytorch(version is 0.2.0_3) from http://pytorch.org/
- Cài đặt bằng đoạn mã sau: (Ở repo này đã clone sẵn file vision này)
```
git clone https://github.com/pytorch/vision
cd vision
python setup.py install
```
## Dataset & Preparation
Download [Market1501 Dataset](http://www.liangzheng.org/Project/project_reid.html)

Bước 1: Chuẩn bị dữ liệu
```bash
python prepare.py
```
Bước 2: Đổi tên của các folder từ 0 đến n-1 (với n là số class, ví dụ như số lượng người) tên folder là nhãn của từng người (tất cả ảnh trong 1 folder cùng là một người) 
```bash
python changeIndex.py
```
Đầu tiên sử dụng market1501 để huấn luyện dcgan, sau đó tạo các hình ảnh sử dụng DCGAN đã được huấn luyện, tiếp theo có thể sử dụng số lượng các hình ảnh khác nhau đó để giúp huấn luyện mô hình sử dụng LSRO

**Hình ảnh được tạo ra được đặt trong folder gen_0000*

Lưu lại mô hình
```bash
mkdir model 
```


## Train
Huấn luyện baseline bằng lệnh
```bash
python train_baseline.py --use_dense
```

`--name` tên model.(ResNet or DesNet)

`--data_dir` đường dẫn đến dữ liệu huấn luyện.

`--batchsize` batch size.

`--erasing_p` random erasing probability.


## Test
Sử dụng model đã huấn luyện để truy xuất feature:
```bash
python test.py   --which_epoch 99  --use_dense
```
`--gpu_ids` là dùng GPU nào để chạy.

`--name` dir name của model đã train.

`--which_epoch` chọn model thứ i.

`--data_dir` đường dẫn đến tập test.

`--batchsize` batch size.


## Evaluation
```bash
python evaluate.py
```
Nó sẽ có output là các kết quả Rank@1, Rank@5, Rank@10 và mAP

Tham khảo cách tính mAP tại[C++ code for Oxford Building](http://www.robots.ox.ac.uk/~vgg/data/oxbuildings/compute_ap.cpp).
Code mẫu này sử dụng triangle mAP calculation (giống với code Market1501 gốc)
### re-ranking
```bash
python evaluate_rerank.py
```
**Có thể sẽ mất bộ nhớ hơn 10GB để chạy** Do vậy nên chạy trên máy có cấu hình mạnh. 

Nó sẽ trả về các kết quả Rank@1, Rank@5, Rank@10 và mAP

### Kết luận

Khi đường baseline không quá cao, hình ảnh được sinh ra có thể giúp mô hình huấn luyện (có thể thấy khi huấn luyện với multi-gpu, thêm các hình ảnh GAN so với không thêm) kết luận cho thấy có thể cải thiện hiệu suất (hơn robust), nhưng khi kết quả đường cơ sở cao(rank-1, 0.934), kết quả rất khó được cải thiện. Với batchsize là 32 kết quả sẽ đạt được tốt nhất, và single-gpu cho kết quả huấn luyện tốt hơn multi-gpu

  
