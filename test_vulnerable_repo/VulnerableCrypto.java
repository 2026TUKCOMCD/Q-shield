// Java - RSA/ECDSA 취약점
import java.security.KeyPairGenerator;
import java.security.Signature;
import javax.crypto.Cipher;

public class VulnerableCrypto {
    
    // 취약점 1: RSA KeyPairGenerator
    public static void generateRSAKey() throws Exception {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
        keyGen.initialize(2048);
        var keyPair = keyGen.generateKeyPair();
    }
    
    // 취약점 2: ECDSA 서명
    public static void signWithECDSA() throws Exception {
        Signature signature = Signature.getInstance("SHA256withECDSA");
        // 서명 로직...
    }
    
    // 취약점 3: RSA Cipher
    public static void encryptWithRSA() throws Exception {
        Cipher cipher = Cipher.getInstance("RSA/ECB/PKCS1Padding");
        // 암호화 로직...
    }
}
