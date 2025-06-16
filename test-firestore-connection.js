// Firestore接続テスト
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, getDocs } from 'firebase/firestore';

const firebaseConfig = {
  projectId: "hackathon-462905",
  authDomain: "hackathon-462905.firebaseapp.com",
  storageBucket: "hackathon-462905.appspot.com",
  messagingSenderId: "269567634217",
  appId: "YOUR_APP_ID_HERE"  // Firebase Console から取得したもの
};

async function testFirestoreConnection() {
  try {
    const app = initializeApp(firebaseConfig);
    const db = getFirestore(app);
    
    console.log('🔍 Firestore接続テスト開始...');
    
    // 全コレクション名を試す
    const collectionNames = ['influencers', 'channels', 'youtubers', 'user_settings'];
    
    for (const collectionName of collectionNames) {
      try {
        const querySnapshot = await getDocs(collection(db, collectionName));
        console.log(`📁 ${collectionName}: ${querySnapshot.size} documents`);
        
        if (querySnapshot.size > 0) {
          querySnapshot.forEach((doc) => {
            console.log(`  - ${doc.id}:`, Object.keys(doc.data()));
          });
        }
      } catch (error) {
        console.log(`❌ ${collectionName}: アクセスエラー`);
      }
    }
    
  } catch (error) {
    console.error('❌ Firestore接続失敗:', error);
  }
}

// ブラウザのコンソールで実行
testFirestoreConnection();