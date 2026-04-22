"use client";

import { useState } from "react";
import { Zap, Gem } from "lucide-react";
import useXpBoostStore, { XP_BOOST_COST } from "@/stores/xpBoostStore";
import useGemsStore from "@/stores/gemsStore";
import toast from "react-hot-toast";

export default function ActivateBoostButton({ variant = "default" }) {
  const {
    availableBoosts,
    isActive,
    canActivate,
    activateBoost,
    addBoost,
  } = useXpBoostStore();
  const { gems, spendGems } = useGemsStore();
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);

  const handleActivate = () => {
    try {
      activateBoost();
      toast.success("🔥 XP Boost đã kích hoạt! x2 XP trong 15 phút!");
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handlePurchase = () => {
    try {
      spendGems(XP_BOOST_COST, "Mua XP Boost");
      addBoost(1);
      setShowPurchaseModal(false);
      toast.success(`✨ Đã mua XP Boost! (${availableBoosts + 1} boosts)`);
    } catch (error) {
      toast.error("Không đủ Gems!");
    }
  };

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-2">
        {availableBoosts > 0 && !isActive && (
          <button
            onClick={handleActivate}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:scale-105 hover:shadow-xl"
          >
            <Zap className="h-4 w-4 fill-white" />
            Kích hoạt x2 XP
          </button>
        )}
        
        <button
          onClick={() => setShowPurchaseModal(true)}
          className="flex items-center gap-2 rounded-lg border border-yellow-500 bg-white px-4 py-2 text-sm font-semibold text-yellow-600 transition-all hover:bg-yellow-50 dark:bg-gray-800 dark:text-yellow-400 dark:hover:bg-gray-700"
        >
          <Gem className="h-4 w-4" />
          Mua Boost ({availableBoosts})
        </button>

        {showPurchaseModal && (
          <PurchaseModal
            onClose={() => setShowPurchaseModal(false)}
            onPurchase={handlePurchase}
            gems={gems}
            cost={XP_BOOST_COST}
          />
        )}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold text-foreground">XP Boost</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Nhân đôi XP trong 15 phút
          </p>
        </div>
        <div className="rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 p-3">
          <Zap className="h-6 w-6 fill-white text-white" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-foreground">
            {availableBoosts}
          </div>
          <div className="text-xs text-muted-foreground">Boosts có sẵn</div>
        </div>

        {isActive ? (
          <div className="rounded-lg bg-green-100 px-4 py-2 dark:bg-green-900/30">
            <div className="text-xs font-medium text-green-700 dark:text-green-400">
              ✓ Đang hoạt động
            </div>
          </div>
        ) : availableBoosts > 0 ? (
          <button
            onClick={handleActivate}
            className="rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:scale-105"
          >
            Kích hoạt
          </button>
        ) : (
          <button
            onClick={() => setShowPurchaseModal(true)}
            className="flex items-center gap-2 rounded-lg border border-yellow-500 px-4 py-2 text-sm font-semibold text-yellow-600 transition-all hover:bg-yellow-50 dark:text-yellow-400 dark:hover:bg-gray-700"
          >
            <Gem className="h-4 w-4" />
            {XP_BOOST_COST} Gems
          </button>
        )}
      </div>

      {showPurchaseModal && (
        <PurchaseModal
          onClose={() => setShowPurchaseModal(false)}
          onPurchase={handlePurchase}
          gems={gems}
          cost={XP_BOOST_COST}
        />
      )}
    </div>
  );
}

function PurchaseModal({ onClose, onPurchase, gems, cost }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-800" onClick={(e) => e.stopPropagation()}>
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-yellow-500 to-orange-500">
            <Zap className="h-8 w-8 fill-white text-white" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Mua XP Boost</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Nhân đôi XP trong 15 phút tiếp theo
          </p>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-muted p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Giá:</span>
            <div className="flex items-center gap-1.5">
              <Gem className="h-4 w-4 fill-blue-400 text-blue-500" />
              <span className="font-bold text-foreground">{cost}</span>
            </div>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Số dư:</span>
            <div className="flex items-center gap-1.5">
              <Gem className="h-4 w-4 fill-blue-400 text-blue-500" />
              <span className={`font-bold ${gems >= cost ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                {gems}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
          >
            Hủy
          </button>
          <button
            onClick={onPurchase}
            disabled={gems < cost}
            className="flex-1 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
          >
            Mua ngay
          </button>
        </div>
      </div>
    </div>
  );
}

