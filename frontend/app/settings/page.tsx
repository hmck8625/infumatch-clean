'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import Header from '@/components/Header';
// UserSettings型定義を追加
interface UserSettings {
  userId: string;
  companyInfo: {
    companyName: string;
    industry: string;
    employeeCount: string;
    website: string;
    description: string;
    contactPerson?: string;
    contactEmail?: string;
  };
  products: Array<{
    id: string;
    name: string;
    category: string;
    targetAudience: string;
    priceRange: string;
    description: string;
  }>;
  negotiationSettings: {
    preferredTone: string;
    responseTimeExpectation: string;
    budgetFlexibility: string;
    decisionMakers: string[];
    communicationPreferences: string[];
    specialInstructions?: string;
    keyPriorities?: string[];
    avoidTopics?: string[];
  };
  matchingSettings: {
    priorityCategories: string[];
    minSubscribers: number;
    maxSubscribers: number;
    minEngagementRate: number;
    excludeCategories: string[];
    geographicFocus: string[];
    priorityKeywords?: string[];
    excludeKeywords?: string[];
  };
  createdAt: string;
  updatedAt: string;
}
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Save, 
  Settings, 
  Package, 
  DollarSign, 
  AlertTriangle,
  User,
  Building,
  Mail,
  Target,
  MessageSquare,
  CheckCircle,
  Info,
  LogOut
} from 'lucide-react';


interface ProductInfo {
  id: string;
  name: string;
  category: string;
  description: string;
  targetAudience: string;
  keyFeatures: string[];
  priceRange: {
    min: number;
    max: number;
    currency: string;
  };
  campaignTypes: string[];
}

interface NegotiationSettings {
  defaultBudgetRange: {
    min: number;
    max: number;
  };
  negotiationTone: 'friendly' | 'professional' | 'assertive';
  keyPriorities: string[];
  avoidTopics: string[];
  specialInstructions: string;
  maxNegotiationRounds: number;
  autoApprovalThreshold: number;
}

interface MatchingPreferences {
  preferredChannelTypes: string[];
  minimumSubscribers: number;
  maximumSubscribers: number;
  preferredCategories: string[];
  geographicPreferences: string[];
  ageGroups: string[];
  excludeKeywords: string[];
  priorityKeywords: string[];
}

// 🎯 デフォルト設定データ
const getDefaultSettings = (): UserSettings => ({
  userId: '',
  companyInfo: {
    companyName: 'InfuMatch株式会社',
    industry: 'マーケティング・テクノロジー',
    employeeCount: '10-50名',
    website: 'https://infumatch.com',
    description: 'YouTubeインフルエンサーと企業を繋ぐAIマッチングプラットフォームを提供しています。',
    contactPerson: '田中美咲',
    contactEmail: 'contact@infumatch.com'
  },
  products: [
    {
      id: '1',
      name: 'スマートフィットネスアプリ',
      category: 'フィットネス・健康',
      targetAudience: '20-40代、健康志向の男女',
      priceRange: '月額980円',
      description: 'AI技術を活用したパーソナルトレーニングアプリ。ユーザーの運動レベルに合わせて最適なワークアウトプランを提案します。'
    },
    {
      id: '2', 
      name: 'オーガニック美容液',
      category: '美容・コスメ',
      targetAudience: '25-45歳女性、美容意識の高い層',
      priceRange: '3,980円-12,800円',
      description: '100%天然成分で作られた高品質美容液。敏感肌にも優しく、エイジングケアに効果的な成分を厳選配合。'
    }
  ],
  negotiationSettings: {
    preferredTone: 'friendly',
    responseTimeExpectation: '48時間以内',
    budgetFlexibility: 'medium',
    decisionMakers: ['マーケティング部長', 'CMO'],
    communicationPreferences: ['email', 'ビデオ通話'],
    specialInstructions: '長期的なパートナーシップを重視し、コンテンツの質を最優先に考えています。',
    keyPriorities: ['ブランドイメージ適合性', 'エンゲージメント率', '長期関係構築'],
    avoidTopics: ['政治的発言', '競合他社との比較']
  },
  matchingSettings: {
    priorityCategories: ['フィットネス', '美容・コスメ', 'ライフスタイル'],
    minSubscribers: 10000,
    maxSubscribers: 500000,
    minEngagementRate: 3.0,
    excludeCategories: ['ギャンブル', '成人向けコンテンツ'],
    geographicFocus: ['日本'],
    priorityKeywords: ['健康', '美容', 'ライフスタイル', 'レビュー'],
    excludeKeywords: ['炎上', '批判', '悪評']
  },
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
});

export default function SettingsPage() {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [hasUserData, setHasUserData] = useState(false); // ユーザーデータ存在フラグ
  
  const [settings, setSettings] = useState<UserSettings>(getDefaultSettings());

  const [newProduct, setNewProduct] = useState({
    name: '',
    category: '',
    description: '',
    targetAudience: '',
    priceRange: '0円〜10万円' // 文字列として管理
  });

  useEffect(() => {
    if (status === 'authenticated') {
      loadSettings();
    } else if (status === 'loading') {
      // まだ読み込み中
      return;
    } else {
      // 未認証の場合はローディングを停止
      setIsLoading(false);
    }
  }, [status]);

  const loadSettings = async () => {
    try {
      console.log('📞 Loading user settings...');
      const response = await fetch('/api/settings');
      
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          console.log('✅ Settings loaded successfully');
          
          // ユーザーデータが存在するかチェック
          const hasUserSettings = result.data.companyInfo?.companyName || 
                                  result.data.products?.length > 0 ||
                                  result.data.negotiationSettings?.specialInstructions;
          
          if (hasUserSettings) {
            // ユーザーデータが存在する場合：デフォルトとマージ
            console.log('🔄 Merging user data with defaults');
            const defaultSettings = getDefaultSettings();
            const mergedSettings = {
              ...defaultSettings,
              ...result.data,
              companyInfo: { ...defaultSettings.companyInfo, ...result.data.companyInfo },
              products: result.data.products?.length > 0 ? result.data.products : defaultSettings.products,
              negotiationSettings: { ...defaultSettings.negotiationSettings, ...result.data.negotiationSettings },
              matchingSettings: { ...defaultSettings.matchingSettings, ...result.data.matchingSettings }
            };
            
            setSettings(mergedSettings);
            setHasUserData(true);
            console.log('👤 Using saved user settings');
          } else {
            // ユーザーデータが存在しない場合：デフォルト設定使用
            console.log('📝 Using default settings');
            setSettings(getDefaultSettings());
            setHasUserData(false);
            setSaveMessage('デフォルト設定を表示しています。お好みに合わせて編集・保存してください。');
          }
        } else {
          console.error('❌ Failed to load settings:', result.error);
          setSettings(getDefaultSettings());
          setHasUserData(false);
          setSaveMessage('デフォルト設定を使用しています。');
        }
      } else {
        console.error('❌ API Error:', response.status);
        setSettings(getDefaultSettings());
        setHasUserData(false);
        setSaveMessage('デフォルト設定を使用しています。');
      }
    } catch (error) {
      console.error('❌ Settings load error:', error);
      setSettings(getDefaultSettings());
      setHasUserData(false);
      setSaveMessage('デフォルト設定を使用しています。');
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setIsSaving(true);
      console.log('💾 Saving settings...');
      
      const response = await fetch('/api/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        console.log('✅ Settings saved successfully');
        setSaveMessage('設定が正常に保存されました');
        setHasUserData(true); // 保存後はユーザーデータありに設定
        if (result.data) {
          setSettings(result.data);
        }
        setTimeout(() => setSaveMessage(null), 3000);
      } else {
        console.error('❌ Save failed:', result.error);
        setSaveMessage(`保存エラー: ${result.error || '不明なエラー'}`);
        setTimeout(() => setSaveMessage(null), 5000);
      }
    } catch (error) {
      console.error('❌ Settings save error:', error);
      setSaveMessage('保存中にエラーが発生しました');
      setTimeout(() => setSaveMessage(null), 5000);
    } finally {
      setIsSaving(false);
    }
  };

  const addProduct = () => {
    if (!newProduct.name) return;
    
    const product = {
      id: Date.now().toString(),
      name: newProduct.name || '',
      category: newProduct.category || '',
      description: newProduct.description || '',
      targetAudience: newProduct.targetAudience || '',
      priceRange: newProduct.priceRange || '0円〜10万円'
    };
    
    setSettings(prev => ({
      ...prev,
      products: [...prev.products, product]
    }));
    
    // フォームリセット
    setNewProduct({
      name: '',
      category: '',
      description: '',
      targetAudience: '',
      priceRange: '0円〜10万円'
    });
  };

  const removeProduct = (productId: string) => {
    setSettings(prev => ({
      ...prev,
      products: prev.products.filter(p => p.id !== productId)
    }));
  };

  const addToArray = (path: string, value: string) => {
    if (!value.trim()) return;
    
    setSettings(prev => {
      const newSettings = { ...prev };
      const pathArray = path.split('.');
      let current: any = newSettings;
      
      for (let i = 0; i < pathArray.length - 1; i++) {
        current = current[pathArray[i]];
      }
      
      const finalKey = pathArray[pathArray.length - 1];
      if (!current[finalKey].includes(value.trim())) {
        current[finalKey] = [...current[finalKey], value.trim()];
      }
      
      return newSettings;
    });
  };

  const removeFromArray = (path: string, value: string) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const pathArray = path.split('.');
      let current: any = newSettings;
      
      for (let i = 0; i < pathArray.length - 1; i++) {
        current = current[pathArray[i]];
      }
      
      const finalKey = pathArray[pathArray.length - 1];
      current[finalKey] = current[finalKey].filter((item: string) => item !== value);
      
      return newSettings;
    });
  };

  // 認証状態のローディング中
  if (status === 'loading' || (status === 'authenticated' && isLoading)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">{status === 'loading' ? '認証状態を確認中...' : '設定を読み込み中...'}</p>
        </div>
      </div>
    );
  }

  // 未認証の場合はログインページへのリダイレクト案内
  if (status === 'unauthenticated') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <User className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">ログインが必要です</h2>
          <p className="text-gray-600 mb-6">
            設定ページにアクセスするには、まずログインしてください。
          </p>
          <Link href="/auth/signin" className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
            <User className="w-4 h-4 mr-2" />
            ログインページに移動
          </Link>
        </div>
      </div>
    );
  }

  const saveSettingsAction = (
    <Button onClick={saveSettings} disabled={isSaving} className="btn-primary">
      {isSaving ? (
        <>
          <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
          保存中...
        </>
      ) : (
        <>
          <Save className="w-4 h-4 mr-2" />
          設定を保存
        </>
      )}
    </Button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* ヘッダー */}
      <Header variant="glass" extraActions={saveSettingsAction} />

      <main className="container mx-auto px-6 py-8">
        {/* ヘッダーセクション */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mr-4">
              <Settings className="w-8 h-8 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">
                設定管理
              </h1>
              <p className="text-xl text-gray-600">
                AIマッチング・交渉機能をカスタマイズ
              </p>
            </div>
          </div>
        </div>

        {saveMessage && (
          <Alert className={`mb-6 ${saveMessage.includes('エラー') ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription className={saveMessage.includes('エラー') ? 'text-red-800' : 'text-green-800'}>
              {saveMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* 設定状態インジケーター */}
        <Alert className={`mb-6 ${hasUserData ? 'border-blue-200 bg-blue-50' : 'border-yellow-200 bg-yellow-50'}`}>
          <Info className="h-4 w-4" />
          <AlertDescription className={hasUserData ? 'text-blue-800' : 'text-yellow-800'}>
            {hasUserData ? 
              '💾 保存された設定を表示しています' : 
              '📝 デフォルト設定を表示しています。お好みに合わせて編集・保存してください。'
            }
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="company" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="company">企業情報</TabsTrigger>
            <TabsTrigger value="products">商材管理</TabsTrigger>
            <TabsTrigger value="negotiation">交渉設定</TabsTrigger>
            <TabsTrigger value="matching">マッチング設定</TabsTrigger>
          </TabsList>

          {/* 企業情報タブ */}
          <TabsContent value="company">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Building className="w-5 h-5 mr-2" />
                  企業基本情報
                </CardTitle>
                <CardDescription>
                  AIマッチングと交渉で使用される企業情報を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="company-name">企業名 *</Label>
                    <Input
                      id="company-name"
                      value={settings.companyInfo.companyName}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        companyInfo: { ...prev.companyInfo, companyName: e.target.value }
                      }))}
                      placeholder="株式会社InfuMatch"
                    />
                  </div>
                  <div>
                    <Label htmlFor="industry">業界</Label>
                    <Input
                      id="industry"
                      value={settings.companyInfo.industry}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        companyInfo: { ...prev.companyInfo, industry: e.target.value }
                      }))}
                      placeholder="マーケティング・広告"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">企業説明</Label>
                  <Textarea
                    id="description"
                    value={settings.companyInfo.description}
                    onChange={(e) => setSettings(prev => ({ 
                      ...prev, 
                      companyInfo: { ...prev.companyInfo, description: e.target.value }
                    }))}
                    placeholder="YouTubeインフルエンサーマーケティングプラットフォームを提供しています..."
                    rows={4}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="contact-person">担当者名</Label>
                    <Input
                      id="contact-person"
                      value={settings.companyInfo.contactPerson || ''}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        companyInfo: { ...prev.companyInfo, contactPerson: e.target.value }
                      }))}
                      placeholder="田中 太郎"
                    />
                  </div>
                  <div>
                    <Label htmlFor="contact-email">連絡先メールアドレス</Label>
                    <Input
                      id="contact-email"
                      type="email"
                      value={settings.companyInfo.contactEmail || ''}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        companyInfo: { ...prev.companyInfo, contactEmail: e.target.value }
                      }))}
                      placeholder="contact@infumatch.com"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 商材管理タブ */}
          <TabsContent value="products">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Package className="w-5 h-5 mr-2" />
                    商材情報管理
                  </CardTitle>
                  <CardDescription>
                    AIマッチングで使用される商材情報を管理します
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* 登録済み商材一覧 */}
                  {settings.products.length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-semibold mb-4">登録済み商材</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {settings.products.map((product) => (
                          <div key={product.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium">{product.name}</h5>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => removeProduct(product.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                削除
                              </Button>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{product.description}</p>
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline">{product.category}</Badge>
                              <span className="text-xs text-gray-500">
                                {product.priceRange || '価格未設定'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <Separator className="my-6" />
                    </div>
                  )}

                  {/* 新規商材追加フォーム */}
                  <div>
                    <h4 className="font-semibold mb-4">新規商材追加</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <Label htmlFor="product-name">商品・サービス名 *</Label>
                        <Input
                          id="product-name"
                          value={newProduct.name}
                          onChange={(e) => setNewProduct(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="新商品A"
                        />
                      </div>
                      <div>
                        <Label htmlFor="product-category">カテゴリ</Label>
                        <Input
                          id="product-category"
                          value={newProduct.category}
                          onChange={(e) => setNewProduct(prev => ({ ...prev, category: e.target.value }))}
                          placeholder="食品・飲料"
                        />
                      </div>
                    </div>

                    <div className="mb-4">
                      <Label htmlFor="product-description">商品説明</Label>
                      <Textarea
                        id="product-description"
                        value={newProduct.description}
                        onChange={(e) => setNewProduct(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="健康に配慮した新しい調味料です..."
                        rows={3}
                      />
                    </div>

                    <div className="mb-4">
                      <Label htmlFor="target-audience">ターゲット層</Label>
                      <Input
                        id="target-audience"
                        value={newProduct.targetAudience}
                        onChange={(e) => setNewProduct(prev => ({ ...prev, targetAudience: e.target.value }))}
                        placeholder="20-40代女性、料理好き"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="col-span-2">
                        <Label htmlFor="price-range">価格帯</Label>
                        <Input
                          id="price-range"
                          type="text"
                          placeholder="例: 1万円〜10万円"
                          value={newProduct.priceRange || ''}
                          onChange={(e) => setNewProduct(prev => ({ 
                            ...prev, 
                            priceRange: e.target.value
                          }))}
                        />
                      </div>
                    </div>

                    <Button onClick={addProduct} disabled={!newProduct.name}>
                      <Package className="w-4 h-4 mr-2" />
                      商材を追加
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 交渉設定タブ */}
          <TabsContent value="negotiation">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  AI交渉エージェント設定
                </CardTitle>
                <CardDescription>
                  交渉エージェントの動作をカスタマイズします
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 予算設定 */}
                <div>
                  <h4 className="font-semibold mb-4 flex items-center">
                    <DollarSign className="w-4 h-4 mr-2" />
                    デフォルト予算範囲
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="budget-min">最小予算（円）</Label>
                      <Input
                        id="budget-min"
                        type="number"
                        value={settings.matchingSettings.minSubscribers}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          matchingSettings: {
                            ...prev.matchingSettings,
                            minSubscribers: parseInt(e.target.value) || 1000
                          }
                        }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="budget-max">最大予算（円）</Label>
                      <Input
                        id="budget-max"
                        type="number"
                        value={settings.matchingSettings.maxSubscribers}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          matchingSettings: {
                            ...prev.matchingSettings,
                            maxSubscribers: parseInt(e.target.value) || 1000000
                          }
                        }))}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* 交渉トーン */}
                <div>
                  <h4 className="font-semibold mb-4">交渉トーン</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { value: 'friendly', label: '親しみやすい', desc: '明るく親近感のある口調' },
                      { value: 'professional', label: 'プロフェッショナル', desc: '丁寧で礼儀正しい口調' },
                      { value: 'assertive', label: '積極的', desc: '自信に満ちた力強い口調' }
                    ].map((tone) => (
                      <div
                        key={tone.value}
                        onClick={() => setSettings(prev => ({
                          ...prev,
                          negotiationSettings: {
                            ...prev.negotiationSettings,
                            preferredTone: tone.value
                          }
                        }))}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          settings.negotiationSettings.preferredTone === tone.value
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <h5 className="font-medium mb-1">{tone.label}</h5>
                        <p className="text-sm text-gray-600">{tone.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                {/* 交渉時の留意点 */}
                <div>
                  <h4 className="font-semibold mb-4 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    交渉時の特別指示
                  </h4>
                  <Textarea
                    value={settings.negotiationSettings.specialInstructions || ''}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      negotiationSettings: {
                        ...prev.negotiationSettings,
                        specialInstructions: e.target.value
                      }
                    }))}
                    placeholder="交渉時に留意すべき点や特別な指示を記入してください..."
                    rows={4}
                  />
                </div>

                {/* 重要ポイント */}
                <div>
                  <h4 className="font-semibold mb-4">交渉で重視するポイント</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(settings.negotiationSettings.keyPriorities || []).map((priority, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-red-50"
                        onClick={() => removeFromArray('negotiationSettings.keyPriorities', priority)}
                      >
                        {priority} ×
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="重視するポイントを入力"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addToArray('negotiationSettings.keyPriorities', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        addToArray('negotiationSettings.keyPriorities', input.value);
                        input.value = '';
                      }}
                    >
                      追加
                    </Button>
                  </div>
                </div>

                {/* 避けるべきトピック */}
                <div>
                  <h4 className="font-semibold mb-4">避けるべきトピック</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(settings.negotiationSettings.avoidTopics || []).map((topic, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-red-50"
                        onClick={() => removeFromArray('negotiationSettings.avoidTopics', topic)}
                      >
                        {topic} ×
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="避けるべきトピックを入力"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addToArray('negotiationSettings.avoidTopics', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        addToArray('negotiationSettings.avoidTopics', input.value);
                        input.value = '';
                      }}
                    >
                      追加
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* マッチング設定タブ */}
          <TabsContent value="matching">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  AIマッチング設定
                </CardTitle>
                <CardDescription>
                  自動マッチングの条件をカスタマイズします
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 登録者数範囲 */}
                <div>
                  <h4 className="font-semibold mb-4">チャンネル登録者数範囲</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="min-subscribers">最小登録者数</Label>
                      <Input
                        id="min-subscribers"
                        type="number"
                        value={settings.matchingSettings.minSubscribers}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          matchingSettings: {
                            ...prev.matchingSettings,
                            minSubscribers: parseInt(e.target.value) || 1000
                          }
                        }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="max-subscribers">最大登録者数</Label>
                      <Input
                        id="max-subscribers"
                        type="number"
                        value={settings.matchingSettings.maxSubscribers}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          matchingSettings: {
                            ...prev.matchingSettings,
                            maxSubscribers: parseInt(e.target.value) || 1000000
                          }
                        }))}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* 優先カテゴリ */}
                <div>
                  <h4 className="font-semibold mb-4">優先チャンネルカテゴリ</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(settings.matchingSettings.priorityCategories || []).map((category, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-red-50"
                        onClick={() => removeFromArray('matchingSettings.priorityCategories', category)}
                      >
                        {category} ×
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="優先カテゴリを入力（例：料理、美容、ゲーム）"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addToArray('matchingSettings.priorityCategories', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        addToArray('matchingSettings.priorityCategories', input.value);
                        input.value = '';
                      }}
                    >
                      追加
                    </Button>
                  </div>
                </div>

                {/* 優先キーワード */}
                <div>
                  <h4 className="font-semibold mb-4">優先キーワード</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(settings.matchingSettings.priorityKeywords || []).map((keyword, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-red-50"
                        onClick={() => removeFromArray('matchingSettings.priorityKeywords', keyword)}
                      >
                        {keyword} ×
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="優先キーワードを入力"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addToArray('matchingSettings.priorityKeywords', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        addToArray('matchingSettings.priorityKeywords', input.value);
                        input.value = '';
                      }}
                    >
                      追加
                    </Button>
                  </div>
                </div>

                {/* 除外キーワード */}
                <div>
                  <h4 className="font-semibold mb-4">除外キーワード</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(settings.matchingSettings.excludeKeywords || []).map((keyword, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="cursor-pointer hover:bg-red-50"
                        onClick={() => removeFromArray('matchingSettings.excludeKeywords', keyword)}
                      >
                        {keyword} ×
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="除外キーワードを入力"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          addToArray('matchingSettings.excludeKeywords', e.currentTarget.value);
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        addToArray('matchingSettings.excludeKeywords', input.value);
                        input.value = '';
                      }}
                    >
                      追加
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* 保存確認エリア */}
        <Card className="mt-8 border-amber-200 bg-amber-50">
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <Info className="w-6 h-6 text-amber-600" />
              <div className="flex-1">
                <h4 className="font-semibold text-amber-800">設定の保存について</h4>
                <p className="text-sm text-amber-700">
                  設定を変更した後は、右上の「設定を保存」ボタンをクリックしてください。
                  これらの設定はAIマッチングと交渉エージェントで自動的に活用されます。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}