# Linux Ubuntu ve Windows için Çift Ön Yüklemede (Dual Boot) Bluetooth Cihazları Eşleştirme Rehberi

## Giriş
Bu kılavuz, bluetooth cihazları aynı bilgisayar üzerinde çift ön yükleme (dual boot) ortamında hem Windows hem de Linux Ubuntu üzerinde kullanabilmek için komutları içermektedir. Bu dosya, [Pairing bluetooth devices in dual boot with Linux Ubuntu and Windows 10/11](https://gist.github.com/madkoding/f3cfd3742546d5c99131fd19ca267fd4) temel alınarak Türkçeye çevrilmiş ve küçük eklemeler yapılmıştır. 

### 1. Önce Linux'ta eşleştirin
- Bluetooth cihazınızı ilk olarak Linux'ta eşleştirin. Bu, LinkKey'in geçerli kalmasını sağlamak için çok önemlidir.
- **Not**: Windows'ta eşleştirmeyi tamamladıktan sonra cihazı Linux'ta yeniden eşleştirmeyin. Çünkü Windows'ta eşleştirme yaptıktan sonra eşleştirme anahtarını Linux'ta manuel olarak değiştireceğiz.

### 2. Windows'ta eşleştirin
- Bluetooth cihazını Windows'ta eşleştirin. Daha sonraki adımlar için cihazın MAC adresini not edin (Linux'a geçtiğinizde buna ihtiyacınız olacak). 

### 3. Linux'ta `chntpw` yükleyin
- Windows kayıt defteri anahtarlarını okumak için `chntpw` paketini yükleyin:
  ```bash
  sudo apt-get install chntpw
  ```

### 4. Linux'ta Windows Sistem Diski'ne Erişim
- Windows sistem diskini bağlayın ve System32 yapılandırma klasörüne gidin:
  ```bash
  cd /[MountedDrive]/Windows/System32/config
  ```

### 5. Kayıt Defterine (Registry) Erişmek için `chntpw` komutunu kullanın
- config klasöründe aşağıdaki komutu çalıştırın:
  ```bash
  chntpw -e SYSTEM
  ```
![image](https://gist.github.com/user-attachments/assets/3028cfa0-0904-41b3-8542-37f7614ba49f)

### 6. Bluetooth Kayıt Defteri Anahtarlarına gidin
- `chntpw` konsolunda, Bluetooth kayıt defteri anahtarlarına gidin:
  ```bash
  cd \ControlSet001\Services\BTHPORT\Parameters\Keys
  ```
  
### 7. Eşleştirme Anahtarını Bulun ve Kopyalayın
- Unique ID'leri listelemek için `ls` komutunu kullanın.
![image](https://gist.github.com/user-attachments/assets/b8eb87b2-ddb1-4649-b16a-00c5ac0c4342)

- Cihazınızla ilişkili eşleştirme anahtarını (hex kodu) alın. Bunun için öncelikle `ls` komutu ile listelediğiniz MAC adresine gidin.
  ```bash
  cd <your_device_key_id>
  ```
- `ls` komutunu tekrar çalıştırın. Aşağıdaki gibi bir liste göreceksiniz, bu liste Windows'ta bağladığınız Bluetooth cihazlarının listesi. 
![image](https://gist.github.com/user-attachments/assets/53be11de-9407-464b-98bb-c696e2ce92d4)

- REG_BINARY değerini kopyalayın ve `hex <value>` çalıştırın (value Bluetooth cihazınızın MAC adresi şeklinde olan) çıktı şu şekilde olmalıdır:
  ```bash
     (...)\BTHPORT\Parameters\Keys\mac> hex val
  Value <val> of type REG_BINARY (3), data length 16 [0x10]
  :00000  xx xx xx yy zz aa bb cc dd .E.{..<./*......
  ```
- Buradaki 32 haneli değeri kopyalayıp boşlukları silin. Sonuç değer yukarıdaki çıktıya göre `xxxxxxyyzzaabbccdd` şeklinde olmalıdır.

### 8. Linux Bluetooth Dosyasını Düzenleyin
- Linux sürücünüzdeki ilgili dosyayı düzenleyin:
  ```bash
  sudo nano /var/lib/bluetooth/[Unique ID]/[Mac Address]/info
  ```
- `[LinkKey]` bölümündeki `Key` değerini Windowsdaki eşleştirme anahtarı ile değiştirin.
- Eğer `[LinkKey]` bölümü eksikse, manuel olarak ekleyin.
![image](https://gist.github.com/user-attachments/assets/d6feb2ae-482c-4103-9cfe-a6317f400196)



### 9. Linux'ta Bluetooth Hizmetini Yeniden Başlatın
- Değişiklikleri kaydedin ve Bluetooth hizmetini yeniden başlatın:
  ```bash
  sudo service bluetooth restart
  ```

