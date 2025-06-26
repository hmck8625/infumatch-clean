'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Save, 
  Settings, 
  Bot, 
  AlertTriangle,
  Clock,
  Shield,
  Zap,
  CheckCircle,
  XCircle,
  ArrowLeft,
  Info
} from 'lucide-react';

interface AutoNegotiationSettings {
  enabled: boolean;
  maxRounds: number;
  autoApprovalThreshold: number;
  budgetFlexibilityLimit: number;
  responseTimeLimit: number;
  workingHours: {
    start: number;
    end: number;
  };
  maxDailyNegotiations: number;
  escalationConditions: string[];
  emergencyStopKeywords: string[];
  riskToleranceLevel: 'conservative' | 'balanced' | 'aggressive';
}

export default function AutoNegotiationSettingsPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState<AutoNegotiationSettings>({
    enabled: false,
    maxRounds: 3,
    autoApprovalThreshold: 75,
    budgetFlexibilityLimit: 15,
    responseTimeLimit: 24,
    workingHours: {
      start: 9,
      end: 18
    },
    maxDailyNegotiations: 10,
    escalationConditions: [
      'budget_exceeded',
      'negative_sentiment',
      'complex_terms',
      'max_rounds_reached'
    ],
    emergencyStopKeywords: [
      'キャンセル',
      '中止',
      '法的措置',
      '弁護士',
      '訴訟'
    ],
    riskToleranceLevel: 'balanced'
  });

  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      // 設定を読み込み（現在はローカルストレージから）
      const saved = localStorage.getItem('autoNegotiationSettings');
      if (saved) {
        setSettings(JSON.parse(saved));
      }
    } catch (error) {
      console.error('設定の読み込みに失敗:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      // 設定を保存（現在はローカルストレージに）
      localStorage.setItem('autoNegotiationSettings', JSON.stringify(settings));
      
      // 将来的にはバックエンドAPIに送信
      // await fetch('/api/settings/auto-negotiation', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(settings)
      // });
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('設定の保存に失敗:', error);
      alert('設定の保存に失敗しました');
    } finally {
      setIsSaving(false);
    }
  };

  const updateSettings = (key: keyof AutoNegotiationSettings, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const addEscalationCondition = (condition: string) => {
    if (!settings.escalationConditions.includes(condition)) {
      updateSettings('escalationConditions', [...settings.escalationConditions, condition]);
    }
  };

  const removeEscalationCondition = (condition: string) => {
    updateSettings('escalationConditions', 
      settings.escalationConditions.filter(c => c !== condition)
    );
  };

  const addEmergencyKeyword = (keyword: string) => {
    if (keyword.trim() && !settings.emergencyStopKeywords.includes(keyword.trim())) {
      updateSettings('emergencyStopKeywords', [...settings.emergencyStopKeywords, keyword.trim()]);
    }
  };

  const removeEmergencyKeyword = (keyword: string) => {
    updateSettings('emergencyStopKeywords', 
      settings.emergencyStopKeywords.filter(k => k !== keyword)
    );
  };

  const escalationConditionLabels = {
    'budget_exceeded': '予算超過',
    'negative_sentiment': 'ネガティブ感情検出',
    'complex_terms': '複雑な条件・法的用語',
    'max_rounds_reached': '最大ラウンド数到達',
    'urgent_decision_required': '緊急判断必要',
    'competitor_mention': '競合他社への言及',
    'brand_safety_concerns': 'ブランド安全性の懸念'
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Header />
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Button 
              variant="ghost" 
              onClick={() => router.push('/settings')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              設定に戻る
            </Button>
          </div>
          
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl text-white">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">自動交渉エージェント設定</h1>
              <p className="text-gray-600">AI が自動でインフルエンサーとの交渉を行う設定を管理</p>
            </div>
          </div>

          {/* 状態表示 */}
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
              settings.enabled 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              {settings.enabled ? (
                <>
                  <CheckCircle className="h-4 w-4" />
                  自動交渉有効
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4" />
                  自動交渉無効
                </>
              )}
            </div>
            
            {settings.enabled && (
              <Badge variant="secondary" className="flex items-center gap-1">
                <Zap className="h-3 w-3" />
                最大 {settings.maxRounds} ラウンド
              </Badge>
            )}
          </div>
        </div>

        {/* 設定タブ */}
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full">
            <TabsTrigger value="basic">基本設定</TabsTrigger>
            <TabsTrigger value="safety">安全機構</TabsTrigger>
            <TabsTrigger value="schedule">スケジュール</TabsTrigger>
            <TabsTrigger value="advanced">詳細設定</TabsTrigger>
          </TabsList>

          {/* 基本設定 */}
          <TabsContent value="basic" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  基本設定
                </CardTitle>
                <CardDescription>
                  自動交渉システムの基本的な動作を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 自動交渉有効化 */}
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-base font-medium">自動交渉を有効化</Label>
                    <p className="text-sm text-gray-600">
                      AIが自動でインフルエンサーとの交渉を行います
                    </p>
                  </div>
                  <Switch
                    checked={settings.enabled}
                    onCheckedChange={(checked) => updateSettings('enabled', checked)}
                  />
                </div>

                <Separator />

                {/* 最大ラウンド数 */}
                <div className="space-y-3">
                  <Label className="text-base font-medium">最大交渉ラウンド数</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[settings.maxRounds]}
                      onValueChange={(value) => updateSettings('maxRounds', value[0])}
                      max={5}
                      min={1}
                      step={1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>1回</span>
                      <span className="font-medium text-purple-600">
                        {settings.maxRounds}回
                      </span>
                      <span>5回</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    この回数を超えると人間の介入が必要になります
                  </p>
                </div>

                <Separator />

                {/* 自動承認しきい値 */}
                <div className="space-y-3">
                  <Label className="text-base font-medium">自動承認しきい値</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[settings.autoApprovalThreshold]}
                      onValueChange={(value) => updateSettings('autoApprovalThreshold', value[0])}
                      max={95}
                      min={50}
                      step={5}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>50%</span>
                      <span className="font-medium text-purple-600">
                        {settings.autoApprovalThreshold}%
                      </span>
                      <span>95%</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    AIの信頼度がこの値を超えた場合に自動送信されます
                  </p>
                </div>

                <Separator />

                {/* 予算柔軟性上限 */}
                <div className="space-y-3">
                  <Label className="text-base font-medium">予算柔軟性上限</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[settings.budgetFlexibilityLimit]}
                      onValueChange={(value) => updateSettings('budgetFlexibilityLimit', value[0])}
                      max={30}
                      min={5}
                      step={5}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>5%</span>
                      <span className="font-medium text-purple-600">
                        {settings.budgetFlexibilityLimit}%
                      </span>
                      <span>30%</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    設定予算からこの割合を超えた交渉は人間の承認が必要です
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 安全機構 */}
          <TabsContent value="safety" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  エスカレーション条件
                </CardTitle>
                <CardDescription>
                  人間の介入が必要になる条件を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(escalationConditionLabels).map(([key, label]) => (
                    <div
                      key={key}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        settings.escalationConditions.includes(key)
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => {
                        if (settings.escalationConditions.includes(key)) {
                          removeEscalationCondition(key);
                        } else {
                          addEscalationCondition(key);
                        }
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-4 h-4 rounded border-2 ${
                          settings.escalationConditions.includes(key)
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-gray-300'
                        }`}>
                          {settings.escalationConditions.includes(key) && (
                            <CheckCircle className="w-4 h-4 text-white" />
                          )}
                        </div>
                        <span className="text-sm font-medium">{label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  緊急停止キーワード
                </CardTitle>
                <CardDescription>
                  これらのキーワードが検出されると自動交渉を即座に停止します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {settings.emergencyStopKeywords.map((keyword, index) => (
                    <Badge
                      key={index}
                      variant="destructive"
                      className="cursor-pointer"
                      onClick={() => removeEmergencyKeyword(keyword)}
                    >
                      {keyword} ×
                    </Badge>
                  ))}
                </div>
                
                <div className="flex gap-2">
                  <Input
                    placeholder="新しいキーワードを追加"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addEmergencyKeyword((e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = '';
                      }
                    }}
                  />
                  <Button
                    variant="outline"
                    onClick={(e) => {
                      const input = e.currentTarget.parentElement?.querySelector('input');
                      if (input) {
                        addEmergencyKeyword(input.value);
                        input.value = '';
                      }
                    }}
                  >
                    追加
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* スケジュール設定 */}
          <TabsContent value="schedule" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  稼働時間設定
                </CardTitle>
                <CardDescription>
                  自動交渉が動作する時間帯を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 稼働時間 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>開始時間</Label>
                    <Input
                      type="number"
                      min="0"
                      max="23"
                      value={settings.workingHours.start}
                      onChange={(e) => updateSettings('workingHours', {
                        ...settings.workingHours,
                        start: parseInt(e.target.value)
                      })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>終了時間</Label>
                    <Input
                      type="number"
                      min="0"
                      max="23"
                      value={settings.workingHours.end}
                      onChange={(e) => updateSettings('workingHours', {
                        ...settings.workingHours,
                        end: parseInt(e.target.value)
                      })}
                    />
                  </div>
                </div>
                
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">
                    現在の設定: {settings.workingHours.start}:00 〜 {settings.workingHours.end}:00
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    稼働時間外の交渉は翌営業時間に処理されます
                  </p>
                </div>

                <Separator />

                {/* 日次上限 */}
                <div className="space-y-3">
                  <Label className="text-base font-medium">1日の最大自動交渉数</Label>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    value={settings.maxDailyNegotiations}
                    onChange={(e) => updateSettings('maxDailyNegotiations', parseInt(e.target.value))}
                  />
                  <p className="text-sm text-gray-600">
                    この数を超えると翌日まで自動交渉が停止されます
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 詳細設定 */}
          <TabsContent value="advanced" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>リスク許容レベル</CardTitle>
                <CardDescription>
                  自動交渉時のリスク許容度を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { key: 'conservative', label: '保守的', desc: '安全性重視' },
                    { key: 'balanced', label: 'バランス', desc: '中間的なアプローチ' },
                    { key: 'aggressive', label: '積極的', desc: '効率性重視' }
                  ].map((option) => (
                    <div
                      key={option.key}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        settings.riskToleranceLevel === option.key
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => updateSettings('riskToleranceLevel', option.key)}
                    >
                      <div className="text-center">
                        <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${
                          settings.riskToleranceLevel === option.key
                            ? 'bg-purple-500'
                            : 'bg-gray-300'
                        }`} />
                        <div className="font-medium">{option.label}</div>
                        <div className="text-xs text-gray-600">{option.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                設定変更後は、進行中の交渉には適用されません。新しい交渉から有効になります。
              </AlertDescription>
            </Alert>
          </TabsContent>
        </Tabs>

        {/* 保存ボタン */}
        <div className="flex justify-end gap-4">
          <Button
            variant="outline"
            onClick={() => router.push('/settings')}
          >
            キャンセル
          </Button>
          <Button
            onClick={saveSettings}
            disabled={isSaving}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
          >
            {isSaving ? (
              <>保存中...</>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                設定を保存
              </>
            )}
          </Button>
        </div>

        {/* 成功メッセージ */}
        {saveSuccess && (
          <Alert className="mt-4 border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              設定を正常に保存しました
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}