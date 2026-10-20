"use client";

import React, { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  PrintableStation,
  WorksheetPrintConfig,
} from "./types";
import {
  RUBRIC_DIMENSIONS,
  EXIT_TICKET_QUESTIONS,
} from "./worksheetData";
import { cn } from "@/lib/utils";

interface PrintableFieldworkWorksheetProps {
  stations: PrintableStation[];
  config: WorksheetPrintConfig;
  className?: string;
}

export default function PrintableFieldworkWorksheet({
  stations,
  config,
  className,
}: PrintableFieldworkWorksheetProps) {
  const [origin, setOrigin] = useState("https://luuniensuki.vn");

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.origin) {
      setOrigin(window.location.origin);
    }
  }, []);

  const isTeacher = config.teacher_key_mode;
  const isLandscape = config.orientation === "landscape";

  return (
    <div
      id="fieldwork-printable-area"
      className={cn(
        "printable-worksheet bg-white text-black font-sans leading-relaxed selection:bg-amber-200",
        isLandscape ? "print-landscape w-[297mm] min-h-[210mm]" : "print-portrait w-[210mm] min-h-[297mm]",
        "mx-auto p-6 md:p-8 space-y-6 shadow-sm border border-neutral-300 print:border-none print:shadow-none print:m-0 print:p-0",
        className,
      )}
      style={{
        colorAdjust: "exact",
        WebkitPrintColorAdjust: "exact",
      }}
    >
      {/* ============================================================== */}
      {/* 1. ADMINISTRATIVE HEADER (Công văn 5512/BGDĐT)                 */}
      {/* ============================================================== */}
      <header className="border-b-2 border-black pb-4 space-y-3 avoid-break">
        <div className="grid grid-cols-2 gap-4 items-start text-xs">
          {/* Top Left: School & Ministry */}
          <div className="space-y-0.5 text-left font-serif">
            <p className="font-semibold uppercase tracking-wider text-[11px] text-neutral-700">
              SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ
            </p>
            <p className="font-bold uppercase text-[12px] text-black">
              {config.school_name || "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ"}
            </p>
            <p className="italic text-[11px] text-neutral-800">
              Tổ chuyên môn: {config.department_name || "Lịch sử - Địa lý"}
            </p>
            <p className="font-mono text-[10px] text-neutral-600 mt-1">
              Mã hồ sơ: <span className="font-bold text-black">{config.lesson_code || "KHTN-LS10-DN01"}</span> (Công văn 5512/BGDĐT)
            </p>
          </div>

          {/* Top Right: National Motto */}
          <div className="space-y-0.5 text-center font-serif">
            <p className="font-bold uppercase text-[11px] tracking-wide text-black">
              CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
            </p>
            <p className="font-semibold text-[11px] text-neutral-800">
              Độc lập – Tự do – Hạnh phúc
            </p>
            <div className="w-28 mx-auto border-b border-black pt-1" />
            <p className="text-[10px] text-neutral-600 italic pt-1">
              Huế, ngày ...... tháng ...... năm 202...
            </p>
          </div>
        </div>

        {/* Central Title */}
        <div className="text-center pt-2 space-y-1">
          <div className="inline-block px-3 py-0.5 border border-black rounded text-[10px] font-bold uppercase tracking-wider bg-neutral-100 text-black">
            {isTeacher
              ? "HỒ SƠ GIÁO VIÊN — HƯỚNG DẪN CHẤM & ĐÁP ÁN CHUẨN (TEACHER KEY)"
              : "PHIẾU HỌC TẬP THỰC ĐỊA — BẢN LÀM BÀI CỦA HỌC SINH"}
          </div>
          <h1 className="font-serif font-black text-lg md:text-xl uppercase tracking-tight text-black">
            PHIẾU ĐIỀN DÃ DI SẢN: KHÁM PHÁ KHÔNG GIAN & ĐỐI CHIẾU SỬ LIỆU ĐẠI NỘI HUẾ
          </h1>
          <p className="text-[11px] italic text-neutral-700 max-w-3xl mx-auto">
            Chủ đề: Trật tự không gian, kiến trúc cung đình và phê phán tư liệu chính sử triều Nguyễn • Mô hình thu thập chứng cứ M-E-E
          </p>
        </div>

        {/* Student Identification & Direct QR Area */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2 items-center bg-neutral-50 p-2.5 rounded border border-neutral-300">
          <div className="md:col-span-9 grid grid-cols-2 sm:grid-cols-3 gap-y-2 gap-x-3 text-xs">
            <div>
              <span className="font-semibold text-neutral-700">Họ và tên HS: </span>
              <span className="font-mono font-bold text-black border-b border-dotted border-black inline-block min-w-[130px]">
                {config.student_name || "..................................................."}
              </span>
            </div>
            <div>
              <span className="font-semibold text-neutral-700">Lớp: </span>
              <span className="font-mono font-bold text-black border-b border-dotted border-black inline-block min-w-[70px]">
                {config.class_name || "10 Sử"}
              </span>
            </div>
            <div>
              <span className="font-semibold text-neutral-700">Nhóm điền dã: </span>
              <span className="font-mono border-b border-dotted border-black inline-block min-w-[70px]">
                ....................
              </span>
            </div>
            <div>
              <span className="font-semibold text-neutral-700">Ngày điền dã: </span>
              <span className="font-mono border-b border-dotted border-black inline-block min-w-[90px]">
                {config.date_vi || "...../...../202..."}
              </span>
            </div>
            <div>
              <span className="font-semibold text-neutral-700">Giáo viên phụ trách: </span>
              <span className="font-mono border-b border-dotted border-black inline-block min-w-[110px]">
                {config.teacher_name || "...................................."}
              </span>
            </div>
            <div className="bg-white px-2 py-1 border border-black rounded text-center">
              <span className="font-bold text-[10px] text-neutral-800 uppercase block">
                Điểm Rubric S1-S4:
              </span>
              <span className="font-serif font-black text-sm text-black">
                {isTeacher ? "12 / 12 (Đáp án)" : "........... / 12"}
              </span>
            </div>
          </div>

          {/* Scannable Header QR directing to /dai-noi interactive aerial map */}
          {config.include_qr && (
            <div className="md:col-span-3 flex items-center gap-2 border-l border-neutral-300 pl-3">
              <div className="bg-white p-1 border border-neutral-400 rounded shrink-0">
                <QRCodeSVG
                  value={`${origin}/dai-noi`}
                  size={58}
                  level="M"
                  includeMargin={true}
                />
              </div>
              <div className="text-[9px] leading-tight text-neutral-600">
                <span className="font-bold text-black uppercase block">Bản đồ số Đại Nội:</span>
                Quét QR để mở không ảnh trực giao & định vị tọa độ GPS thực địa.
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ============================================================== */}
      {/* 2. INSTRUCTIONS BOX                                             */}
      {/* ============================================================== */}
      <section className="text-[11px] bg-neutral-100/70 border border-neutral-300 p-2.5 rounded avoid-break">
        <p className="font-semibold text-black">
          📌 <span className="underline">Quy tắc ghi chép điền dã theo mô hình M-E-E:</span>
        </p>
        <p className="text-neutral-800 mt-0.5 leading-snug">
          Mỗi trạm quan sát gồm 4 cột bắt buộc: <strong>(1) Vị trí trên bản đồ</strong>; <strong>(2) Hiện trạng mắt thấy</strong>; <strong>(3) Tư liệu chính sử đối chiếu</strong>; <strong>(4) Em kết luận gì</strong> (chỉ rõ <em>Mệnh đề</em> khẳng định, <em>Bằng chứng</em> đối chiếu và <em>Điều cần kiểm chứng thêm</em>). Tuyệt đối tuân thủ chuẩn mực sử học &quot;nói có sách, mách có chứng&quot;.
        </p>
      </section>

      {/* ============================================================== */}
      {/* 3. THE 4-COLUMN EVIDENCE TABLE                                  */}
      {/* ============================================================== */}
      <section className="space-y-4">
        <div className="overflow-x-visible">
          <table className="w-full border-collapse border-2 border-black text-[11px]">
            <thead>
              <tr className="bg-neutral-200 text-black border-b-2 border-black font-serif">
                <th className="border border-black p-2 text-left w-[20%] font-bold">
                  <div className="text-[9px] uppercase font-mono tracking-wider text-neutral-700">CỘT 1</div>
                  <span>TRẠM QUAN SÁT & VỊ TRÍ TRÊN BẢN ĐỒ</span>
                  <div className="text-[9px] font-sans font-normal text-neutral-600 mt-0.5">
                    Tên di tích, phân khu, trục tọa độ Thần đạo
                  </div>
                </th>
                <th className="border border-black p-2 text-left w-[26%] font-bold">
                  <div className="text-[9px] uppercase font-mono tracking-wider text-neutral-700">CỘT 2</div>
                  <span>HIỆN TRẠNG MẮT THẤY TẠI THỰC ĐỊA</span>
                  <div className="text-[9px] font-sans font-normal text-neutral-600 mt-0.5">
                    Mặt bằng, số tầng, số cửa, vật liệu, tình trạng bảo tồn
                  </div>
                </th>
                <th className="border border-black p-2 text-left w-[27%] font-bold">
                  <div className="text-[9px] uppercase font-mono tracking-wider text-neutral-700">CỘT 3</div>
                  <span>TƯ LIỆU CHÍNH SỬ ĐỐI CHIẾU</span>
                  <div className="text-[9px] font-sans font-normal text-neutral-600 mt-0.5">
                    Đại Nam Thực Lục, Hội Điển, Nhất Thống Chí, ảnh EFEO
                  </div>
                </th>
                <th className="border border-black p-2 text-left w-[27%] font-bold">
                  <div className="text-[9px] uppercase font-mono tracking-wider text-neutral-700">CỘT 4</div>
                  <span>EM KẾT LUẬN GÌ (MÔ HÌNH M - E - E)</span>
                  <div className="text-[9px] font-sans font-normal text-neutral-600 mt-0.5">
                    Mệnh đề (M) • Bằng chứng (E) • Giới hạn kiểm chứng (E)
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {stations.map((st, index) => {
                const stationDirectUrl = `${origin}${st.digital_coordinate_hint || `/dai-noi/cong-trinh/${st.monument_slug}`}`;
                return (
                  <tr
                    key={st.monument_slug || index}
                    className="border-b border-black avoid-break align-top hover:bg-neutral-50/50"
                  >
                    {/* CỘT 1: TRẠM QUAN SÁT & VỊ TRÍ */}
                    <td className="border border-black p-2.5 bg-neutral-50/80 space-y-1.5">
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-mono text-[10px] font-bold px-1.5 py-0.2 rounded bg-black text-white">
                          TRẠM {index + 1}
                        </span>
                        {st.reign && (
                          <span className="text-[9px] text-neutral-600 italic">
                            Triều {st.reign}
                          </span>
                        )}
                      </div>

                      <div className="font-serif font-bold text-sm text-black leading-tight">
                        {st.monument_name_vi}
                      </div>

                      <p className="text-[10px] text-neutral-700 leading-tight">
                        {st.zone_name_vi}
                      </p>

                      {st.construction_year && (
                        <p className="text-[9px] text-neutral-600 font-mono">
                          Khởi dựng: <strong>{st.construction_year}</strong>
                        </p>
                      )}

                      {/* Station specific QR Code for direct fieldwork check */}
                      {config.include_qr && (
                        <div className="pt-1.5 flex items-center gap-1.5 border-t border-neutral-300">
                          <div className="bg-white p-0.5 border border-black rounded shrink-0">
                            <QRCodeSVG
                              value={stationDirectUrl}
                              size={44}
                              level="M"
                              includeMargin={true}
                            />
                          </div>
                          <div className="text-[8px] leading-tight text-neutral-600">
                            <span className="font-semibold text-black block">Hồ sơ số 3D:</span>
                            Quét xem ảnh vệ tinh & tư liệu đa tầng
                          </div>
                        </div>
                      )}
                    </td>

                    {/* CỘT 2: HIỆN TRẠNG MẮT THẤY */}
                    <td className="border border-black p-2.5 space-y-2">
                      <div className="text-[10px] text-neutral-800 italic bg-neutral-100 p-1 rounded border border-neutral-200">
                        <strong>Nhiệm vụ quan sát:</strong> {st.observation_prompt_vi}
                      </div>

                      {isTeacher ? (
                        <div className="p-1.5 rounded bg-emerald-50 border border-emerald-300 text-[10px] text-emerald-950 space-y-1">
                          <span className="font-bold text-[9px] uppercase tracking-wider text-emerald-800 block">
                            [Gợi ý hiện trạng mắt thấy - Giáo viên]:
                          </span>
                          <p className="leading-snug">
                            {st.observation_sample_answer_vi}
                          </p>
                        </div>
                      ) : (
                        /* Student handwritten writing lines */
                        <div className="space-y-3.5 pt-1">
                          <div className="text-[9px] text-neutral-600 uppercase font-semibold">
                            Ghi chép hiện trạng tại thực địa:
                          </div>
                          <div className="h-4 border-b border-dotted border-black/70" />
                          <div className="h-4 border-b border-dotted border-black/70" />
                          <div className="h-4 border-b border-dotted border-black/70" />
                          <div className="h-4 border-b border-dotted border-black/70" />
                        </div>
                      )}
                    </td>

                    {/* CỘT 3: TƯ LIỆU CHÍNH SỬ ĐỐI CHIẾU */}
                    <td className="border border-black p-2.5 bg-amber-50/20 space-y-2">
                      <div className="space-y-0.5">
                        <span className="font-serif font-bold text-[11px] text-black block">
                          📖 {st.primary_source.source_title}
                        </span>
                        {st.primary_source.volume_or_chapter && (
                          <span className="text-[9px] font-mono text-neutral-700 block">
                            [{st.primary_source.volume_or_chapter}]
                          </span>
                        )}
                      </div>

                      <blockquote className="p-1.5 rounded bg-neutral-100 border-l-2 border-black text-[10px] italic text-neutral-900 leading-snug">
                        &ldquo;{st.primary_source.citation}&rdquo;
                      </blockquote>

                      {isTeacher ? (
                        <div className="p-1.5 rounded bg-amber-100/70 border border-amber-300 text-[9px] text-amber-950">
                          <strong>Phân tích sử liệu:</strong> Đoạn chép chuẩn bị căn cứ pháp lý & trật tự nghi lễ cấp quốc gia. Yêu cầu học sinh đối chiếu số cửa hoặc số bậc cấp thực tế với quy định trong văn bản.
                        </div>
                      ) : (
                        <div className="space-y-3 pt-1">
                          <div className="text-[9px] text-neutral-600 uppercase font-semibold">
                            Đối chiếu sử liệu với thực tế:
                          </div>
                          <div className="h-4 border-b border-dotted border-black/70" />
                          <div className="h-4 border-b border-dotted border-black/70" />
                        </div>
                      )}
                    </td>

                    {/* CỘT 4: EM KẾT LUẬN GÌ (M-E-E) */}
                    <td className="border border-black p-2.5 bg-blue-50/20 space-y-2">
                      {isTeacher ? (
                        <div className="space-y-1.5 text-[10px]">
                          <div className="p-1.5 rounded bg-blue-50 border border-blue-200">
                            <span className="font-bold text-[9px] text-blue-900 uppercase block">
                              ❖ Mệnh đề lịch sử (Claim - 1đ):
                            </span>
                            <p className="text-neutral-900 leading-snug mt-0.5">
                              {st.mee_claim_sample_vi}
                            </p>
                          </div>
                          <div className="p-1.5 rounded bg-emerald-50 border border-emerald-200">
                            <span className="font-bold text-[9px] text-emerald-900 uppercase block">
                              ❖ Bằng chứng đối chiếu (Evidence - 1đ):
                            </span>
                            <p className="text-neutral-900 leading-snug mt-0.5">
                              {st.mee_evidence_sample_vi}
                            </p>
                          </div>
                          <div className="p-1.5 rounded bg-amber-50 border border-amber-200">
                            <span className="font-bold text-[9px] text-amber-900 uppercase block">
                              ❖ Giới hạn kiểm chứng thêm (Epistemic Boundary - 1đ):
                            </span>
                            <p className="text-neutral-900 leading-snug mt-0.5 italic">
                              {st.mee_uncertainty_sample_vi}
                            </p>
                          </div>
                        </div>
                      ) : (
                        /* Student M-E-E writing sections */
                        <div className="space-y-2 text-[10px]">
                          <div>
                            <span className="font-bold text-[9px] text-neutral-900 uppercase block">
                              ❖ M — Điều em khẳng định chắc chắn (Mệnh đề):
                            </span>
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                          </div>

                          <div>
                            <span className="font-bold text-[9px] text-neutral-900 uppercase block">
                              ❖ E — Bằng chứng mắt thấy + Sử liệu:
                            </span>
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                          </div>

                          <div>
                            <span className="font-bold text-[9px] text-neutral-900 uppercase block">
                              ❖ E — Điều còn cần kiểm chứng thêm (Giả thuyết):
                            </span>
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                            <div className="h-4 border-b border-dotted border-black/70 mt-1" />
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* ============================================================== */}
      {/* 4. EXIT TICKET SECTION (Thu hoạch nhanh 5 phút)                */}
      {/* ============================================================== */}
      {config.include_exit_ticket && (
        <section className="avoid-break border-2 border-black rounded p-3 space-y-2.5 bg-neutral-50/70">
          <div className="flex items-center justify-between border-b border-black/60 pb-1.5">
            <h3 className="font-serif font-bold text-xs uppercase tracking-tight text-black flex items-center gap-1.5">
              <span>🎯 PHẦN THU HOẠCH PHẢN TƯ (EXIT TICKET — 5 PHÚT CUỐI GIỜ)</span>
            </h3>
            <span className="text-[10px] text-neutral-600 italic">
              Đánh giá mức độ hiểu sâu kiến thức không gian & phương pháp sử học
            </span>
          </div>

          <div className="space-y-3 text-[11px]">
            {EXIT_TICKET_QUESTIONS.map((q, idx) => (
              <div key={q.id} className="space-y-1">
                <p className="font-semibold text-black leading-snug">
                  Câu {idx + 1}: {q.question_vi}
                </p>

                {isTeacher && q.sample_answer_vi ? (
                  <div className="p-2 rounded bg-emerald-50 border border-emerald-300 text-[10px] text-emerald-950">
                    <span className="font-bold text-emerald-800 uppercase text-[9px] block">
                      [Gợi ý đáp án]:
                    </span>
                    <p className="leading-snug mt-0.5">{q.sample_answer_vi}</p>
                  </div>
                ) : (
                  <div className="space-y-2.5 pt-0.5">
                    {Array.from({ length: q.space_for_answer_lines || 3 }).map((_, lIdx) => (
                      <div
                        key={lIdx}
                        className="h-3.5 border-b border-dotted border-black/70"
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ============================================================== */}
      {/* 5. RUBRIC S1 - S4 DIRECT PAPER SCORING BOX FOR TEACHER          */}
      {/* ============================================================== */}
      {config.include_rubric && (
        <section className="avoid-break border-2 border-black rounded p-3 space-y-2.5 bg-white">
          <div className="flex items-center justify-between border-b border-black pb-1.5">
            <div>
              <h3 className="font-serif font-bold text-xs uppercase tracking-tight text-black">
                KHUNG ĐÁNH GIÁ NĂNG LỰC LỊCH SỬ (RUBRIC S1 – S4) DÀNH CHO GIÁO VIÊN
              </h3>
              <p className="text-[9px] text-neutral-600">
                Thang điểm 0–3 cho mỗi tiêu chí • Tổng điểm tối đa: 12 điểm
              </p>
            </div>
            <div className="text-[10px] font-mono font-bold px-2 py-0.5 rounded border border-black bg-neutral-100">
              MỨC ĐẠT: ≥ 8/12 (Khá - Tốt)
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-[10px]">
            {RUBRIC_DIMENSIONS.map((dim) => (
              <div
                key={dim.id}
                className="border border-black p-2 rounded bg-neutral-50/60 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between border-b border-neutral-300 pb-1">
                    <span className="font-mono font-bold text-black">{dim.id}</span>
                    <span className="text-[9px] font-semibold text-neutral-600">
                      {dim.dimension}
                    </span>
                  </div>
                  <div className="font-bold text-black text-[10px] mt-1">
                    {dim.name_vi}
                  </div>
                  <p className="text-[9px] text-neutral-700 leading-tight mt-1">
                    {dim.description_vi}
                  </p>
                </div>

                <div className="mt-2 pt-1.5 border-t border-dashed border-neutral-300 flex items-center justify-between">
                  <span className="text-[9px] font-semibold text-neutral-700">Điểm chấm:</span>
                  <div className="flex items-center gap-1 font-mono font-bold">
                    <span className="inline-block w-4 h-4 text-center border border-black rounded text-[9px] leading-4">
                      {isTeacher ? "3" : ""}
                    </span>
                    <span className="text-[9px]">/ 3đ</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Scoring Summary & Feedback Lines */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-1 border-t border-black text-xs items-center">
            <div className="md:col-span-4 flex items-center gap-3">
              <div>
                <span className="font-bold text-[11px] block">TỔNG ĐIỂM:</span>
                <span className="font-serif font-black text-base text-black">
                  {isTeacher ? "12 / 12" : "[       ] / 12"}
                </span>
              </div>
              <div className="text-[9px] text-neutral-700 space-y-0.5 border-l border-neutral-300 pl-2">
                <div>[ ] 11-12: Xuất sắc</div>
                <div>[ ] 8-10: Tốt/Khá</div>
                <div>[ ] 5-7: Đạt</div>
                <div>[ ] 0-4: Cần rèn thêm</div>
              </div>
            </div>

            <div className="md:col-span-8 flex flex-col justify-between">
              <span className="font-semibold text-[10px] text-neutral-800">
                Nhận xét & Chữ ký của giáo viên:
              </span>
              <div className="h-5 border-b border-dotted border-black mt-1" />
              <div className="h-5 border-b border-dotted border-black mt-1" />
            </div>
          </div>
        </section>
      )}

      {/* Footer copyright & curriculum accreditation */}
      <footer className="text-center text-[9px] text-neutral-600 pt-2 border-t border-neutral-300 avoid-break">
        Lưu Niên — Nền tảng học tập di sản số Hoàng Thành Huế • Thiết kế đáp ứng Thông tư 32/2018/TT-BGDĐT & Công văn 5512/BGDĐT.
      </footer>
    </div>
  );
}
