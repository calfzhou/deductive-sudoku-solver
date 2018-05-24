// Copyright 2008 All Rights Reserved.
// Author: Ji ZHOU

#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>
using namespace std;

const int NO_VAL = 0;
const int MAX_SIZE = 35;      // 棋盘最大边长

template <typename T>
struct FlagVar {
  T *pvar;
  T defVal;
  const char *strDefVal;
  const char *desc;

  FlagVar(T *p=NULL, T v=T(), const char *s=NULL, const char *d=NULL)
      : pvar(p), defVal(v), strDefVal(s), desc(d) { }
};

typedef vector<const char*> StrVec;
typedef map<string, FlagVar<bool> > FlagsBool;
typedef map<string, FlagVar<int> > FlagsInt;

template <typename T>
T InitFlag(T &var, T defVal, const char *strDefVal, const char *tag,
           map<string, FlagVar<T> > &flags, const char *desc,
           StrVec &tagsVec) {
  bool temp = true;
  flags[tag] = FlagVar<T>(&var, defVal, strDefVal, desc);
  tagsVec.push_back(tag);
  return defVal;
}

StrVec g_all_tags;
FlagsBool g_flags_bool;
FlagsInt g_flags_int;

#define DEF_FLAG_BOOL(tag, defval, desc)            \
    bool g_##tag = InitFlag<bool>(                  \
        g_##tag, defval, #defval, #tag,             \
        g_flags_bool, desc, g_all_tags);

#define DEF_FLAG_INT(tag, defval, desc)             \
    int g_##tag = InitFlag<int>(                    \
        g_##tag, defval, #defval, #tag,             \
        g_flags_int, desc, g_all_tags);

DEF_FLAG_BOOL(better_print_1, true, "使用棋盘格式打印解棋局。");
DEF_FLAG_BOOL(better_print_2, true, "使用棋盘格式打印未完成棋局。");

DEF_FLAG_BOOL(show_board_deduce, false, "在推导过程中显示棋局。");
DEF_FLAG_BOOL(show_msg_deduce, true, "在推导过程中显示推理信息。");
DEF_FLAG_BOOL(show_board_guess, false, "在猜测过程中显示棋局。");
DEF_FLAG_BOOL(show_msg_guess, false, "在猜测过程中显示推理信息。");

DEF_FLAG_BOOL(disable_naked_deduce, false, "禁用显式规则。");
DEF_FLAG_BOOL(disable_hidden_deduce, false, "禁用隐式规则。");
DEF_FLAG_BOOL(disable_lines_deduce, false, "禁用链列规则。");
DEF_FLAG_BOOL(disable_guess, false, "禁用猜测。");
DEF_FLAG_BOOL(disable_shorten_deduce, false, "禁用规则的短路特性。");

DEF_FLAG_INT(level_naked_deduce, 35, "显式规则等级，[1, 棋盘边长)。");
DEF_FLAG_INT(level_hidden_deduce, 35, "隐式规则等级，[1, 棋盘边长)。");
DEF_FLAG_INT(level_lines_deduce, 35, "链列规则等级，[2, 棋盘边长)。");

DEF_FLAG_INT(max_solution, 10, "最多允许搜索的解数目，[1, )。");

DEF_FLAG_BOOL(help, false, "打印此帮助信息后退出。");

enum Status {S_NORMAL=-1, S_FAILED, S_FINISHED};
#define CHECK_STATUS(res, finished)     do {            \
    if ((res) == S_FAILED) return S_FAILED;             \
    if ((res) == S_NORMAL) finished = false;            \
  } while (false);

inline char Num2Char(int val) {
  if (1 <= val && val <= 9) return val - 1 + '1';
  else if (10 <= val && val <= 35) return val - 10 + 'A';
  else return 'x';
}

inline int Char2Num(char c) {
  if ('1' <= c && c <= '9') return c - '1' + 1;
  else if ('A' <= c && c <= 'Z') return c - 'A' + 10;
  else return 0;
}

// 区域类型，一个区域可以是一行、一列或一个宫格。
typedef int AreaType;
const AreaType AT_BEGIN = 0;  // 区域类型遍历起始
const AreaType AT_ROW   = 0;  // 行
const AreaType AT_COL   = 1;  // 列
const AreaType AT_BLOCK = 2;  // 宫格
const AreaType AT_END   = 3;  // 区域类型遍历终止
const char *AREA_TYPE_STR[] = {
  "行", "列", "块", "区域"
};

// 设置候选数的操作范围。
typedef unsigned int OperRange;
const OperRange OR_CELL       = 0x01;  // 处理指定的方格
const OperRange OR_SAME_AREA  = 0x02;  // 处理指定区域（指定方格以外的方格）
const OperRange OR_OTHER_AREA = 0x04;  // 处理包含指定方格的其他区域（同上）
const OperRange OR_AREA       = 0x06;  // 处理所有包含指定方格的区域（同上）
const OperRange OR_ALL        = 0x07;  // 全部处理

class ShuduSolver {
 public:
  typedef set<int> NumSet;
  typedef pair<int, int> Coor;
  typedef set<Coor> CoorSet;

  // 打印棋局（普通模式），将打印出各方格所有的候选数。
  void PrintBoard(const char *label=NULL) const {
    if (label != NULL && *label != '\0') cout << label << endl;
    for (int xx = 1; xx <= SIZE; ++xx) {
      for (int yy = 1; yy <= SIZE; ++yy) {
        const NumSet &possible = board_[xx-1][yy-1];
        if (mark_[xx-1][yy-1]) {
          cout << Num2Char(*possible.begin());
        } else {
          cout << '[';
          for (NumSet::const_iterator it = possible.begin();
               it != possible.end(); ++it)
            cout << Num2Char(*it);
          cout << ']';
        }
        if (yy < SIZE)
          cout << ((yy % BLOCKY == 0) ? "   " : " ");
      }
      cout << ((xx % BLOCKX == 0 && xx < SIZE) ? "\n\n" : "\n");
    }
    cout << endl;
  }

  // 打印棋局（棋盘模式），只打印出已经确定了数值的方格。
  void PrintBoardMark(const char *label=NULL) const {
    if (!g_better_print_1) return PrintBoard(label);
    if (label != NULL && *label != '\0') cout << label << endl;
    // cout << "┏";
    cout << "+";
    for (int yy = 1; yy <= SIZE; ++yy)
    //   cout << "━" << (yy == SIZE ? "┓" : (yy % BLOCKY == 0 ? "┳" : "┯"));
      cout << "--" << (yy == SIZE ? "-+" : (yy % BLOCKY == 0 ? "-+" : "-+"));
    cout << endl;
    for (int xx = 1; xx <= SIZE; ++xx) {
    //   cout << "┃";
      cout << "|";
      for (int yy = 1; yy <= SIZE; ++yy) {
        const NumSet &possible = board_[xx-1][yy-1];
        cout.width(2);
        if (mark_[xx-1][yy-1]) {
          cout << Num2Char(*possible.begin())
            //    << (yy % BLOCKY == 0 ? "┃" : "│");
               << (yy % BLOCKY == 0 ? " |" : " :");
        } else {
          cout << ""
            //    << (yy % BLOCKY == 0 ? "┃" : "│");
               << (yy % BLOCKY == 0 ? " |" : " :");
        }
      }
      cout << endl;
      if (xx < SIZE) {
        // cout << (xx % BLOCKX == 0 ? "┣" : "┠");
        cout << (xx % BLOCKX == 0 ? "+" : "+");
        for (int yy = 1; yy <= SIZE; ++yy)
          if (xx % BLOCKX == 0) {
            // cout << "━" << (yy == SIZE ? "┫" :
            //      (yy % BLOCKY == 0 ? "╋" : "┿"));
            cout << "--" << (yy == SIZE ? "-+" :
                 (yy % BLOCKY == 0 ? "-+" : "-+"));
          } else {
            // cout << "─" << (yy == SIZE ? "┨" :
            //      (yy % BLOCKY == 0 ? "╂" : "┼"));
            cout << " -" << (yy == SIZE ? " +" :
                 (yy % BLOCKY == 0 ? " +" : " +"));
          }
        cout << endl;
      }
    }
    // cout << "┗";
    cout << "+";
    for (int yy = 1; yy <= SIZE; ++yy)
    //   cout << "━" << (yy == SIZE ? "┛" : (yy % BLOCKY == 0 ? "┻" : "┷"));
      cout << "--" << (yy == SIZE ? "-+" : (yy % BLOCKY == 0 ? "-+" : "-+"));
    cout << "\n" << endl;
  }

  // 打印棋局（棋盘模式），将打印出各方格所有的候选数。
  void PrintBoardAll(const char *label=NULL) const {
    if (!g_better_print_2) return PrintBoard(label);
    if (label != NULL && *label != '\0') cout << label << endl;
    // cout << "┏";
    cout << "+";
    for (int yy = 1; yy <= SIZE; ++yy) {
    //   for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "━";
      for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "--";
    //   cout << (yy == SIZE ? "┓" : (yy % BLOCKY == 0 ? "┳" : "┯"));
      cout << (yy == SIZE ? "-+" : (yy % BLOCKY == 0 ? "-+" : "-+"));
    }
    cout << endl;
    for (int xx = 1; xx <= SIZE; ++xx) {
      for (int xxx = 0; xxx < BLOCKX; ++xxx) {
        // cout << "┃";
        cout << "|";
        for (int yy = 1; yy <= SIZE; ++yy) {
          const NumSet &possible = board_[xx-1][yy-1];
          bool marked = mark_[xx-1][yy-1];
          for (int yyy = 0; yyy < BLOCKY; ++yyy) {
            int val = xxx * BLOCKY + yyy + 1;
            cout.width(2);
            if (possible.find(val) != possible.end()) {
              cout << Num2Char(val);
            } else {
            //   cout << (marked ? "■" : "");
              cout << (marked ? "#" : "");
            }
          }
        //   cout << (yy % BLOCKY == 0 ? "┃" : "│");
          cout << (yy % BLOCKY == 0 ? " |" : " :");
        }
        cout << endl;
      }
      if (xx < SIZE) {
        // cout << (xx % BLOCKX == 0 ? "┣" : "┠");
        cout << (xx % BLOCKX == 0 ? "+" : "+");
        for (int yy = 1; yy <= SIZE; ++yy)
          if (xx % BLOCKX == 0) {
            // for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "━";
            for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "--";
            // cout << (yy == SIZE ? "┫" :
            //      (yy % BLOCKY == 0 ? "╋" : "┿"));
            cout << (yy == SIZE ? "-+" :
                 (yy % BLOCKY == 0 ? "-+" : "-+"));
          } else {
            // for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "─";
            for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << " -";
            // cout << (yy == SIZE ? "┨" :
            //      (yy % BLOCKY == 0 ? "╂" : "┼"));
            cout << (yy == SIZE ? " +" :
                 (yy % BLOCKY == 0 ? " +" : " +"));
          }
        cout << endl;
      }
    }
    // cout << "┗";
    cout << "+";
    for (int yy = 1; yy <= SIZE; ++yy) {
    //   for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "━";
      for (int yyy = 0; yyy < BLOCKY; ++yyy) cout << "--";
    //   cout << (yy == SIZE ? "┛" : (yy % BLOCKY == 0 ? "┻" : "┷"));
      cout << (yy == SIZE ? "-+" : (yy % BLOCKY == 0 ? "-+" : "-+"));
    }
    cout << "\n" << endl;
  }

  ShuduSolver(int blockx, int blocky)
      : BLOCKX(blockx), BLOCKY(blocky), SIZE(BLOCKX * BLOCKY),
      board_(SIZE, vector<NumSet>(SIZE)),
      mark_(SIZE, vector<bool>(SIZE, false)),
      solutionCnt_(0) {
    for (int xx = 0; xx < SIZE; ++xx)
      for (int yy = 0; yy < SIZE; ++yy)
        for (int val = 1; val <= SIZE; ++val)
          board_[xx][yy].insert(val);
  }

  int GetSolutionCnt() const {
    return solutionCnt_;
  }

  // 设置方格(x, y)的数值为val，操作成功后，与此方格同行、列、宫格的其他方格内
  // 的候选数val将被删除。
  Status SetCell(int x, int y, int val) {
    if (val == NO_VAL) return S_FINISHED;
    if (x < 0 || x >= SIZE || y < 0 || y >= SIZE || val < 1 || val > SIZE) {
      cout << "错误：不存在的方格(" << x << ", " << y
           << ")或错误的数值" << Num2Char(val) << "。" << endl;
      return S_FAILED;
    }

    const NumSet &possible = board_[x][y];
    if (mark_[x][y]) {
      if (possible.size() == 1 && possible.find(val) != possible.end())
        return S_FINISHED;
      cout << "错误：方格(" << x << ", " << y
           << "无法被设置为" << Num2Char(val)
           << "，请检查此方格的候选数。" << endl;
      return S_FAILED;
    }

    CoorSet coors;
    coors.insert(Coor(x, y));
    NumSet vals;
    vals.insert(val);
    return SetPossible(coors, vals);
  }

  // 对当前棋盘进行推导，直到推导结束或出现错误。
  // 返回true表示推导结束，false表示出现错误。
  bool Deduce(bool guessing=false) {
    Status res;
    res = DoDeduce(guessing);
    areaStack_.clear();
    return res != S_FAILED;
  }

  // 处理不确定的棋局，搜索可行解。
  // 返回值通常均为false。
  // 此函数在发现棋局无解或找到最多g_max_solution个解后返回。
  // 参数depth表示递归深度。
  bool SolveDoubt(int depth=0) {
    // 在棋盘中寻找第一个出现的候选数个数最少的方格。
    int x = -1, y = -1, minlen = SIZE + 1;
    for (int xx = 0; xx < SIZE; ++xx) {
      for (int yy = 0; yy < SIZE; ++yy) {
        int len = board_[xx][yy].size();
        if (!mark_[xx][yy] && len < minlen) {
          x = xx;
          y = yy;
          minlen = len;
        }
      }
    }
    if (x < 0 || y < 0 || minlen > SIZE) {
      if (!IsOK()) return false;
      PrintBoardMark("得到一个可行解：");
      ++solutionCnt_;
      return true;
    }

    // 备份当前棋局以便回溯。
    Board board = board_;
    Mark mark = mark_;

    // 遍历此方格的所有候选数，搜索可行解。
    const NumSet &possible = board[x][y];
    for (NumSet::const_iterator itp = possible.begin();
         itp != possible.end(); ++itp) {
      cout.width(depth);
      cout << "" << "假设(" << x+1 << ", " << y+1 << ")是"
           << Num2Char(*itp) << "：" << endl;
      if (SetCellAndDeduce(x, y, *itp) && SolveDoubt(depth+1)) {
        if (solutionCnt_ >= g_max_solution) return true;
      }
      board_ = board;
      mark_ = mark;
    }
    return false;
   }

  // 判断是否已经得到解。
  bool IsOK() const {
    for (int xx = 0; xx < SIZE; ++xx) {
      if (!IsOK(xx, xx, AT_ROW)) return false;
      if (!IsOK(xx, xx, AT_COL)) return false;
    }
    for (int xx = 0; xx < SIZE; xx += BLOCKX) {
      for (int yy = 0; yy < SIZE; yy += BLOCKY) {
        if (!IsOK(xx, yy, AT_BLOCK)) return false;
      }
    }
    return true;
  }

 private:
  typedef vector<bool> BoolVec;
  typedef vector<vector<NumSet> > Board;
  typedef vector<vector<bool> > Mark;

  // 区域范围，指一行、一列或一个宫格。
  struct Area {
    AreaType at;  // 区域类型
    Coor lt;      // 区域扫描起点坐标
    Coor rb;      // 区域扫描终点坐标

    Area(AreaType t=AT_END) : at(t) { }
  };
  struct LTArea : public binary_function<const Area&, const Area&, bool> {
    bool operator()(const Area &area1, const Area &area2) {
      if (area1.at < area2.at) return true;
      if (area1.at > area2.at) return false;
      if (area1.lt.first < area2.lt.first) return true;
      if (area1.lt.first > area2.lt.first) return false;
      if (area1.lt.second < area2.lt.second) return true;
      if (area1.lt.second > area2.lt.second) return false;
      return false;
    }
  };

  // 计算包含由coors指定的所有方格的类型为at的区域范围。
  // 返回false表示不存在这样的区域。
  bool CalcArea(const CoorSet &coors, AreaType at, Area &area) const {
    if (coors.empty()) return false;

    const Coor &coor = *coors.begin();
    switch (at) {
      case AT_ROW:
        area.lt.first = coor.first;
        area.rb.first = area.lt.first + 1;
        area.lt.second = 0;
        area.rb.second = area.lt.second + SIZE;
        break;
      case AT_COL:
        area.lt.first = 0;
        area.rb.first = area.lt.first + SIZE;
        area.lt.second = coor.second;
        area.rb.second = area.lt.second + 1;
        break;
      case AT_BLOCK:
        area.lt.first = (coor.first/BLOCKX) * BLOCKX;
        area.rb.first = area.lt.first + BLOCKX;
        area.lt.second = (coor.second/BLOCKY) * BLOCKY;
        area.rb.second = area.lt.second + BLOCKY;
        break;
    }

    area.at = at;
    for (CoorSet::const_iterator it = coors.begin();
         it != coors.end(); ++it) {
      if (it == coors.begin()) continue;
      if (it->first < area.lt.first || it->first >= area.rb.first ||
          it->second < area.lt.second || it->second >= area.rb.second)
        return false;
    }

    return true;
  }

  // 计算包含方格(x, y)的类型为at的区域范围。
  Area CalcArea(int x, int y, AreaType at) const {
    CoorSet coors;
    coors.insert(Coor(x, y));
    Area area;
    CalcArea(coors, at, area);
    return area;
  }

  // 对当前棋盘进行一次推导。
  Status DoDeduce(bool guessing) {
    Status res;
    do {
      if (!g_disable_naked_deduce || !g_disable_hidden_deduce) {
        while (!areaStack_.empty()) {
          const Area &area = *areaStack_.begin();
          bool finished = true;
          if (!g_disable_naked_deduce) {
            res = NakedDeduce(area, guessing);
            CHECK_STATUS(res, finished);
          }
          if (!g_disable_hidden_deduce) {
            res = HiddenDeduce(area, guessing);
            CHECK_STATUS(res, finished);
          }
          if (finished) {
            areaStack_.erase(area);
          } else if ((guessing && g_show_board_guess) ||
                     (!guessing && g_show_board_deduce)) {
            PrintBoardAll("推导步骤：");
          }
        }
      }

      if (g_disable_lines_deduce) break;
      bool finished = true;
      if (finished) {
        res = LinesDeduce(true, guessing);
        CHECK_STATUS(res, finished);
      }
      if (finished) {
        res = LinesDeduce(false, guessing);
        CHECK_STATUS(res, finished);
      }
      if (finished) {
        break;
      } else if ((guessing && g_show_board_guess) ||
                 (!guessing && g_show_board_deduce)) {
        PrintBoardAll("推导步骤：");
      }
    } while (!areaStack_.empty());

    return areaStack_.empty() ? S_FINISHED : S_NORMAL;
  }

  // 在区域area内进行显式推导，使用的规则包括但不限于：
  //  1.唯一候选数法(Singles Candidature, Sole Candidate)：
  //    若某个方格只有唯一的一个候选数，则这个数就是此方格的数值。
  //  2.数对删减法(Naked Pairs)、三链数删减法(Naked Triples)、k链数删减法：
  //    某k个方格内相异的候选数不超过k个，则可从其他方格的候选数中删除这些数；
  //    其他方格是指包含这k个方格的各区域中，这些方格以外的所有方格。
  // 具体地说，此处使用的规则为：
  //  在区域area内任意选取p个方格，他们的候选数之并集包含q个数字：
  //  （即这p个方格内不可能出现其他数字，但这些数字有可能是其他方格的候选数）
  //  1.若 p < q
  //    不做任何处理。
  //  2.若 p = q
  //    显然这q个数字不可能出现在所有包含这p个方格的区域的其他方格内，
  //    因此将这q个数字从其他方格的候选数中删除。
  //    这里p取1、2、3和k分别对应于唯一候选数法、数对删减法、三链数删减法
  //    和k链数删减法。
  //  3.若 p > q
  //    不可能，因为这p个方格中至少有p-q个方格没有数字可放。
  typedef pair<Coor, NumSet> CellInfo;
  struct LTCellInfo
      : public binary_function<const CellInfo&, const CellInfo&, bool> {
    bool operator()(const CellInfo &cellInfo1, const CellInfo &cellInfo2) {
      return cellInfo1.second.size() < cellInfo2.second.size();
    }
  };
  Status NakedDeduce(const Area &area, bool guessing) {
    // 记录每个方格的候选数，忽略已经确定的方格。
    typedef vector<CellInfo> CellInfoVec;
    CellInfoVec cellInfoVec;
    for (int xx = area.lt.first; xx < area.rb.first; ++xx) {
      for (int yy = area.lt.second; yy < area.rb.second; ++yy) {
        if (mark_[xx][yy]) continue;
        cellInfoVec.push_back(CellInfo(Coor(xx, yy), board_[xx][yy]));
      }
    }
    if (cellInfoVec.empty()) return S_FINISHED;
    sort(cellInfoVec.begin(), cellInfoVec.end(), LTCellInfo());

    bool finished = true;
    Status res;
    int levelLimit = min(max(g_level_naked_deduce, 1), SIZE-1);

    // 对方格个数（规则等级）进行遍历。
    int n = 0;
    for (int l = 1; l <= min((int)cellInfoVec.size(), levelLimit); ++l) {
      while (n < cellInfoVec.size() && cellInfoVec[n].second.size() <= l) ++n;
      if (l > n) continue;
      BoolVec tags(l, true);
      tags.insert(tags.end(), n - l, false);
      bool tagsChanged = false;
      do {  // 遍历所有组合
        tagsChanged = false;
        CoorSet coors;
        NumSet vals;
        CellInfoVec::const_iterator iti = cellInfoVec.begin();
        for (BoolVec::const_iterator itt = tags.begin();
             itt != tags.end(); ++itt, ++iti) {
          if (!*itt) continue;
          coors.insert(iti->first);
          vals.insert(iti->second.begin(), iti->second.end());
        }

        int p = coors.size();
        int q = vals.size();
        if (p < q) {
          continue;
        } else if (p > q) {
          return S_FAILED;
        }

        res = SetPossible(coors, vals, area.at, OR_AREA);
        CHECK_STATUS(res, finished);
        if (res == S_NORMAL) {
          if ((guessing && g_show_msg_guess) || (!guessing && g_show_msg_deduce))
            ShowNakedDeduceMsg(coors, vals, area);
          if (!g_disable_shorten_deduce)
            return S_NORMAL;
        }

        n -= l;
        if (!ChangeVecWithTags(cellInfoVec, tags, l)) break;
        tagsChanged = true;
      } while (tagsChanged || prev_permutation(tags.begin(), tags.end()));
    }

    return finished ? S_FINISHED : S_NORMAL;
  }

  // 在区域area内进行隐性推导，使用的规则包括但不限于：
  //  1.隐性唯一候选数法(Hidden Singles Candidature, Unique Candidate)：
  //    若某个数字在区域内各方格的候选数中只出现一次，则候选数包含这个数字的
  //    方格就只能填入此数字。
  //  2.区块删减法(Locked Candidates, Single Sector Candidates)：
  //    若某个数字只出现在区域内的几个方格的候选数中，则可从其他方格的候选数
  //    中删除这个数字；
  //    其他方格是指包含这几个方格的其他区域中，这些方格以外的所有方格。
  //  3.隐性数对删减法(Hidden Pairs)、隐性三链数删减法(Hidden Triples)、
  //  隐性k链数删减法：
  //    若某k个数字只出现在k个方格的候选数中，则可将这些方格的其他候选数删除。
  // 具体地说，此处使用的规则为：
  //  任意选取q个数字，在他们区域area内的候选方格之并集包含p个方格：
  //  （某个数字的候选方格是指区域内候选数包含此数字的方格的集合）
  //  1.若 p < q
  //    不可能，因为这q个数字中至少有q-p个无处可放。
  //  2.若 p = q
  //    显然这p个方格内不可能出现其他数字，其他方格内也不可能出现这q个数字，
  //    因此将这p个方格的其他候选数删除，将这q个数字从其他方格的候选数中删除。
  //    其他方格是指除了area外，包含这p个方格的区域中，这些方格以外的方格。
  //    这里q取1、2、3和k分别对应于隐性唯一候选数法、隐性数对删减法、
  //    隐性三链数删减法和隐性k链数删减法。
  //  3.若 p > q
  //    显然其他方格内不可能出现这q个数字，
  //    因此将这q个数字从其他方格的候选数中删除。（其他方格意义同上）
  //    这里q取1对应于区块删减法。
  typedef pair<int, CoorSet> ValInfo;
  struct LTValInfo
      : public binary_function<const ValInfo&, const ValInfo&, bool> {
    bool operator()(const ValInfo &valInfo1, const ValInfo &valInfo2) {
      return valInfo1.second.size() < valInfo2.second.size();
    }
  };
  Status HiddenDeduce(const Area &area, bool guessing) {
    // 记录每个数字的候选方格，忽略已经确定的方格。
    typedef map<int, CoorSet> ValMap;
    ValMap valMap;
    for (int xx = area.lt.first; xx < area.rb.first; ++xx) {
      for (int yy = area.lt.second; yy < area.rb.second; ++yy) {
        if (mark_[xx][yy]) continue;
        const NumSet &possible = board_[xx][yy];
        for (NumSet::const_iterator it = possible.begin();
             it != possible.end(); ++it)
          valMap[*it].insert(Coor(xx, yy));
      }
    }
    if (valMap.empty()) return S_FINISHED;
    typedef vector<ValInfo> ValInfoVec;
    ValInfoVec valInfoVec(valMap.begin(), valMap.end());
    sort(valInfoVec.begin(), valInfoVec.end(), LTValInfo());

    bool finished = true;
    Status res;
    int levelLimit = min(max(g_level_hidden_deduce, 1), SIZE-1);

    // 对数字个数（规则等级）进行遍历。
    int n = 0;
    for (int l = 1; l <= min((int)valInfoVec.size(), levelLimit); ++l) {
      while (n < valInfoVec.size() && valInfoVec[n].second.size() <= l) ++n;
      if (l > n) continue;
      BoolVec tags(l, true);
      tags.insert(tags.end(), n - l, false);
      bool tagsChanged = false;
      do {  // 遍历所有组合
        tagsChanged = false;
        NumSet vals;
        CoorSet coors;
        ValInfoVec::const_iterator iti = valInfoVec.begin();
        for (BoolVec::const_iterator itt = tags.begin();
             itt != tags.end(); ++itt, ++iti) {
          if (!*itt) continue;
          vals.insert(iti->first);
          coors.insert(iti->second.begin(), iti->second.end());
        }

        int p = coors.size();
        int q = vals.size();
        if (p < q) {
          return S_FAILED;
        } else if (p > q) {
          continue;
        }

        res = SetPossible(coors, vals, area.at, OR_CELL | OR_OTHER_AREA);
        CHECK_STATUS(res, finished);
        if (res == S_NORMAL) {
          if ((guessing && g_show_msg_guess) || (!guessing && g_show_msg_deduce))
            ShowHiddenDeduceMsg(coors, vals, area);
          if (!g_disable_shorten_deduce)
            return S_NORMAL;
        }

        n -= l;
        if (!ChangeVecWithTags(valInfoVec, tags, l)) break;
        tagsChanged = true;
      } while (tagsChanged || prev_permutation(tags.begin(), tags.end()));
    }

    if (!finished) return S_NORMAL;

    // 隐式规则允许 p > q，在此处理。
    valInfoVec.clear();
    valInfoVec.insert(valInfoVec.end(), valMap.begin(), valMap.end());
    levelLimit = min(levelLimit, max(BLOCKX, BLOCKY)) + 1;
    n = valInfoVec.size();
    for (int l = 1; l < min(n, levelLimit); ++l) {
      BoolVec tags(l, true);
      tags.insert(tags.end(), n - l, false);
      do {  // 遍历所有组合
        NumSet vals;
        CoorSet coors;
        ValInfoVec::const_iterator iti = valInfoVec.begin();
        for (BoolVec::const_iterator itt = tags.begin();
             itt != tags.end(); ++itt, ++iti) {
          if (!*itt) continue;
          vals.insert(iti->first);
          coors.insert(iti->second.begin(), iti->second.end());
        }

        int p = coors.size();
        int q = vals.size();
        if (p < q) {
          return S_FAILED;
        } else if (p == q) {
          continue;
        }

        res = SetPossible(coors, vals, area.at, OR_OTHER_AREA);
        CHECK_STATUS(res, finished);
        if (res == S_NORMAL) {
          if ((guessing && g_show_msg_guess) || (!guessing && g_show_msg_deduce))
            ShowHiddenDeduceMsg(coors, vals, area);
          if (!g_disable_shorten_deduce)
            return S_NORMAL;
        }
      } while (prev_permutation(tags.begin(), tags.end()));
    }

    return finished ? S_FINISHED : S_NORMAL;
  }

  // 在棋盘范围内进行链列推导，rowFirst指定以行优先还是以列优先进行处理，
  // 使用的规则包括但不限于：
  //  1. 矩形顶点删减法(X-Wing)、三链列删减法(Swordfish)、k链列删减法：
  //    若某个数字在某k行/列里仅出现在相同的k列/行中，则这k列/行的其他方格内
  //    都不会出现此数字。
  // 具体地说，此处使用的规则为（以行优先为例）：
  //  任意一个数字val，任意选取p行，val在这p行里的候选列之并集包含q列：
  //  （某个数字在某行的候选列是指，这一行的所有方格中，候选数包含此数字的
  //  那些列的集合。）
  //  1.若 p < q
  //    不做任何处理。
  //  2.若 p = q
  //    显然数字val在这些列内不可能出现在其他行，
  //    因此将val从这些列与其他行的交点方格的候选数中删除。
  //    这里p去2、3和k分别对应于矩阵顶点删减法、三链列删减法和k链列删减法。
  //  3.若 p > q
  //    不可能，因为这p行中至少有p-q行无处放置此数。
  typedef pair<int, NumSet> LineInfo;
  struct LTLineInfo
      : public binary_function<const LineInfo&, const LineInfo&, bool> {
    bool operator()(const LineInfo &lineInfo1, const LineInfo &lineInfo2) {
      return lineInfo1.second.size() < lineInfo2.second.size();
    }
  };
  Status LinesDeduce(bool rowFirst, bool guessing) {
    // 记录每个数字在每一行的候选列，忽略已经确定的方格。
    typedef map<int, NumSet> LineMap;
    typedef map<int, LineMap> ValsLineMap;
    ValsLineMap valsLineMap;
    for (int xx = 0; xx < SIZE; ++xx) {
      for (int yy = 0; yy < SIZE; ++yy) {
        if (mark_[xx][yy]) continue;
        const NumSet &possible = board_[xx][yy];
        int line1 = rowFirst ? xx : yy;
        int line2 = rowFirst ? yy : xx;
        for (NumSet::const_iterator it = possible.begin();
             it != possible.end(); ++it)
          valsLineMap[*it][line1].insert(line2);
      }
    }

    bool finished = true;
    Status res;
    int levelLimit = min(max(g_level_lines_deduce, 2), SIZE-1) + 1;

    // 对数字进行遍历。
    typedef vector<LineInfo> LineInfoVec;
    for (ValsLineMap::const_iterator itv = valsLineMap.begin();
         itv != valsLineMap.end(); ++itv) {
      int val = itv->first;
      const LineMap &lineMap = itv->second;
      if (lineMap.empty()) continue;
      LineInfoVec lineInfoVec(lineMap.begin(), lineMap.end());
      sort(lineInfoVec.begin(), lineInfoVec.end(), LTLineInfo());

      // 对行数（规则等级）进行遍历。
      int n = 0;
      for (int l = 2; l < min((int)lineInfoVec.size(), levelLimit); ++l) {
        while (n < lineInfoVec.size() && lineInfoVec[n].second.size() <= l) ++n;
        if (l > n) continue;
        BoolVec tags(l, true);
        tags.insert(tags.end(), n - l, false);
        bool tagsChanged = false;
        do {  // 遍历所有组合
          tagsChanged = false;
          NumSet lines1;
          NumSet lines2;
          LineInfoVec::const_iterator iti = lineInfoVec.begin();
          for (BoolVec::const_iterator itt = tags.begin();
               itt != tags.end(); ++itt, ++iti) {
            if (!*itt) continue;
            lines1.insert(iti->first);
            lines2.insert(iti->second.begin(), iti->second.end());
          }

          int p = lines1.size();
          int q = lines2.size();
          if (p < q) {
            continue;
          } else if (p > q) {
            return S_FAILED;
          }

          res = SetPossible(lines1, lines2, val, rowFirst);
          CHECK_STATUS(res, finished);
          if (res == S_NORMAL) {
            if ((guessing && g_show_msg_guess) || (!guessing && g_show_msg_deduce))
              ShowBoardDeduceMsg(val, lines1, lines2, rowFirst);
            if (!g_disable_shorten_deduce)
              return S_NORMAL;
          }

          n -= l;
          if (!ChangeVecWithTags(lineInfoVec, tags, l)) break;
          tagsChanged = true;
        } while (tagsChanged || prev_permutation(tags.begin(), tags.end()));
      }
    }

    return finished ? S_FINISHED : S_NORMAL;
  }

  template <typename TVec>
  static bool ChangeVecWithTags(TVec &vec, BoolVec &tags, int l) {
    typename TVec::iterator itv = vec.begin();
    int changesRemain = -1;
    for (BoolVec::iterator itt = tags.begin(); itt != tags.end(); ) {
      if (*itt) {
        if (changesRemain == -1) changesRemain = l;
        itt = tags.erase(itt);
        itv = vec.erase(itv);
      } else {
        if (changesRemain > 0) {
          *itt = true;
          --changesRemain;
        }
        ++itt;
        ++itv;
      }
    }
    return changesRemain == 0;
  }

  // 设置候选数，操作成功后：
  // 若OR_CELL被设置，则coors所指定方格的候选数只能在vals范围内；
  // 若OR_AREA被设置，则包含coors所指定方格的各个区域内，其他方格的候选数不会
  // 包含vals中的数值。
  Status SetPossible(const CoorSet &coors, const NumSet &vals,
                     AreaType orgat=AT_END, OperRange range=OR_ALL) {
    bool finished = true;

    if ((range & OR_CELL) != 0 && !coors.empty()) {
      if (coors.size() > vals.size()) return S_FAILED;
      for (CoorSet::const_iterator itc = coors.begin();
           itc != coors.end(); ++itc) {
        NumSet &possible = board_[itc->first][itc->second];
        bool cellModified = false;
        for (NumSet::iterator itp = possible.begin();
             itp != possible.end(); ) {
          if (vals.find(*itp) == vals.end()) {
            possible.erase(itp++);
            cellModified = true;
            finished = false;
          } else {
            ++itp;
          }
        }
        if (possible.empty()) return S_FAILED;
        if (cellModified)
          for (AreaType t = AT_BEGIN; t < AT_END; ++t)
            areaStack_.insert(CalcArea(itc->first, itc->second, t));
      }
    }

    if ((range & OR_AREA) != 0 && !vals.empty()) {
      if (coors.size() < vals.size()) return S_FAILED;
      for (AreaType at = AT_BEGIN; at < AT_END; ++at) {
        if ((at == orgat && (range & OR_SAME_AREA) == 0) ||
            (at != orgat && (range & OR_OTHER_AREA) == 0))
          continue;
        Area area;
        if (!CalcArea(coors, at, area)) continue;
        for (int xx = area.lt.first; xx < area.rb.first; ++xx) {
          for (int yy = area.lt.second; yy < area.rb.second; ++yy) {
            if (coors.find(Coor(xx, yy)) != coors.end()) continue;
            NumSet &possible = board_[xx][yy];
            bool cellModified = false;
            for (NumSet::iterator itp = possible.begin();
                 itp != possible.end(); ) {
              if (vals.find(*itp) != vals.end()) {
                possible.erase(itp++);
                cellModified = true;
                finished = false;
              } else {
                ++itp;
              }
            }
            if (possible.empty()) return S_FAILED;
            if (cellModified)
              for (AreaType t = AT_BEGIN; t < AT_END; ++t)
                areaStack_.insert(CalcArea(xx, yy, t));
          }  // end of for yy in area
        }  // end of for xx in area
      }  // end of for at
    }

    if (coors.size() == 1 && vals.size() == 1) {
      const Coor &coor = *coors.begin();
      mark_[coor.first][coor.second] = true;
    }

    return finished ? S_FINISHED : S_NORMAL;
  }

  // 设置候选数，操作成功后：
  // lines2所指定的列/行中，不在lines1所指定的行/列上的那些方格的
  // 候选数不会包含val。
  // 若rowFirst为true，则lines1指定行号，lines2指定列号。反之亦然。
  Status SetPossible(const NumSet &lines1, const NumSet &lines2, int val,
                     bool rowFirst) {
    if (lines1.size() > lines2.size()) return S_FAILED;
    if (lines1.size() < lines2.size()) return S_FINISHED;
    bool finished = true;

    for (int ii = 0; ii < SIZE; ++ii) {
      if (lines1.find(ii) != lines1.end()) continue;
      for (NumSet::const_iterator itl2 = lines2.begin();
           itl2 != lines2.end(); ++itl2) {
        int x = rowFirst ? ii : *itl2;
        int y = rowFirst ? *itl2 : ii;
        NumSet &possible = board_[x][y];
        bool cellModified = false;
        if (possible.find(val) != possible.end()) {
          possible.erase(val);
          cellModified = true;
          finished = false;
        }
        if (possible.empty()) return S_FAILED;
        if (cellModified)
          for (AreaType t = AT_BEGIN; t < AT_END; ++t)
            areaStack_.insert(CalcArea(x, y, t));
      }
    }

    return finished ? S_FINISHED : S_NORMAL;
  }

  // 设定方格(x, y)的值为val，并在此基础上进行推导。
  // 返回true表示推导完成，false表示出现错误。
  bool SetCellAndDeduce(int x, int y, int val) {
    Status res;
    res = SetCell(x, y, val);
    if (res == S_FAILED) return false;
    if (res == S_FINISHED) return true;
    return Deduce(true);
  }

  // 检查方格(x, y)所在的类型为at的区域是否已经正确求解了。
  bool IsOK(int x, int y, AreaType at) const {
    Area area = CalcArea(x, y, at);
    vector<bool> occurs(SIZE+1, false);

    for (int xx = area.lt.first; xx < area.rb.first; ++xx) {
      for (int yy = area.lt.second; yy < area.rb.second; ++yy) {
        if (!mark_[xx][yy] || board_[xx][yy].size() != 1) return false;
        int val = *board_[xx][yy].begin();
        if (occurs[val]) return false;
        occurs[val] = true;
      }
    }

    for (int val = 1; val <= SIZE; ++val) {
      if (!occurs[val]) return false;
    }

    return true;
  }

  void ShowNakedDeduceMsg(const CoorSet &coors, const NumSet &vals,
                          const Area &area) const {
    cout << "显式 " << AREA_TYPE_STR[area.at]
         << "(" << area.lt.first+1 << "," << area.lt.second+1 << ")-"
         << "(" << area.rb.first << "," << area.rb.second << ") ";
    for (CoorSet::const_iterator itc = coors.begin();
         itc != coors.end(); ++itc)
      cout << "(" << itc->first+1 << "," << itc->second+1 << ")";
    cout << "中只能出现数字";
    for (NumSet::const_iterator itv = vals.begin();
         itv != vals.end(); ++itv)
      cout << (itv == vals.begin() ? "" : ",") << Num2Char(*itv);
    cout << "；从其他方格中删除这些数。" << endl;
  }

  void ShowHiddenDeduceMsg(const CoorSet &coors, const NumSet &vals,
                           const Area &area) const {
    cout << "隐式 " << AREA_TYPE_STR[area.at]
         << "(" << area.lt.first+1 << "," << area.lt.second+1 << ")-"
         << "(" << area.rb.first << "," << area.rb.second << ") 数字";
    for (NumSet::const_iterator itv = vals.begin();
         itv != vals.end(); ++itv)
      cout << (itv == vals.begin() ? "" : ",") << Num2Char(*itv);
    cout << "只能在";
    for (CoorSet::const_iterator itc = coors.begin();
         itc != coors.end(); ++itc)
      cout << "(" << itc->first+1 << "," << itc->second+1 << ")";
    if (coors.size() == vals.size()) {
      cout << "中；删除这些方格的其他候选数" << endl;
    } else {
      cout << "中；从其他区域中删除这些数。" << endl;
    }
  }

  void ShowBoardDeduceMsg(int val, const NumSet &lines1, const NumSet &lines2,
                          bool rowFirst) const {
    const char *type1 = rowFirst ? "行" : "列";
    const char *type2 = rowFirst ? "列" : "行";
    cout << "链列 数字" << Num2Char(val) << "在第";
    for (NumSet::const_iterator itl1 = lines1.begin();
         itl1 != lines1.end(); ++itl1)
      cout << (itl1 == lines1.begin() ? "" : ",") << *itl1+1;
    cout << type1 << "里只能出现在第";
    for (NumSet::const_iterator itl2 = lines2.begin();
         itl2 != lines2.end(); ++itl2)
      cout << (itl2 == lines2.begin() ? "" : ",") << *itl2+1;
    cout << type2 << "；从这些" << type2 << "里其他" << type1
         << "方格的候选数中删除" << Num2Char(val) << "。" << endl;
  }

  const int BLOCKX;   // 一个宫格占多少行
  const int BLOCKY;   // 一个宫格占多少列
  const int SIZE;     // 棋盘边长（宫格大小）
  Board board_;       // 棋局信息（记录每个方格的候选数）
  Mark mark_;         // 棋局信息（记录每个方格是否已经确定）
  int solutionCnt_;   // 已经发现的可行解数目
  set<Area, LTArea> areaStack_; // 记录尚需处理的区域

  void ShowAreaStack() const {
    cout << "areaStack_.size() = " << areaStack_.size() << endl;
    for (set<Area, LTArea>::const_iterator it = areaStack_.begin();
         it != areaStack_.end(); ++it) {
      const Area area = *it;
      cout << AREA_TYPE_STR[area.at] << "("
           << area.lt.first << ", " << area.lt.second << ")-("
           << area.rb.first << ", " << area.rb.second << ")     ";
    }
    cout << endl;
  }
};

void ShowHelp() {
  cout << "\n格式：shudu3.exe [--<flag>[=<value>]] <一个宫格占多少行> "
       << "[<一个宫格占多少列>]\n"
       << "默认宫格大小为 3 * 3 = 9；自定义宫格最小为 2 * 2 = 4，最大为"
       << MAX_SIZE << "个方格。\n"
       << "flag列表：\n";

  const int tagWidth = 24;
  const int defValWidth = 8;
  cout << " ";
  cout.width(tagWidth);
  cout << left << "名称";
  cout.width(defValWidth);
  cout << left << "默认值" << "说明" << endl;

  for (StrVec::const_iterator it = g_all_tags.begin();
       it != g_all_tags.end(); ++it) {
    const char *tag = *it;
    cout << " ";
    cout.width(tagWidth);
    cout << left << tag;
    if (g_flags_bool.find(tag) != g_flags_bool.end()) {
      const FlagVar<bool> &flagVar = g_flags_bool[tag];
      cout.width(defValWidth);
      cout << left << flagVar.strDefVal << flagVar.desc;
    } else if (g_flags_int.find(tag) != g_flags_int.end()) {
      const FlagVar<int> &flagVar = g_flags_int[tag];
      cout.width(defValWidth);
      cout << left << flagVar.strDefVal << flagVar.desc;
    }
    cout << endl;
  }
}

bool Init(int argc, const char **argv, int &blockx, int &blocky) {
  int idx = 1;
  for (; idx < argc; ++idx) {
    string arg(argv[idx]);
    int pos = arg.find("--");
    if (pos == string::npos) break;
    pos = arg.find("=", 2);
    string tag = arg.substr(2, (pos == string::npos) ? pos : pos-2);
    string val = (pos == string::npos) ? "" : arg.substr(pos+1);

    bool foundFlag = false;
    if (g_flags_bool.find(tag) != g_flags_bool.end()) {
      bool &var = *g_flags_bool[tag].pvar;
      if (val.empty() || val[0] == 't' || val[0] == 'T' ||
          atoi(val.c_str()) != 0) {
        var = true;
      } else {
        var = false;
      }
      cout << "设置" << tag << "为" << (var ? "true" : "false") << "。" << endl;
    } else if (g_flags_int.find(tag) != g_flags_int.end()) {
      int &var = *g_flags_int[tag].pvar;
      var = atoi(val.c_str());
      cout << "设置" << tag << "为" << var << "。" << endl;
    } else {
      cout << "无效的参数：" << tag << endl;
    }
  }

  if (g_help) {
    ShowHelp();
    return false;
  }

  if (idx < argc) {
    int bx = atoi(argv[idx++]);
    int by = bx;
    if (idx < argc) by = atoi(argv[idx++]);
    int size = bx * by;
    if (bx > 1 && by > 1 && size > 0 && size <= MAX_SIZE) {
      blockx = bx;
      blocky = by;
    }
  }
  return true;
}

int main(int argc, const char **argv) {
  int blockx = 3;
  int blocky = 3;
  if (!Init(argc, argv, blockx, blocky)) return 1;
  int size = blockx * blocky;
  cout << "\n宫格大小为：" << blockx << "行" << blocky
       << "列，棋盘边长" << size << "。" << endl;
  cout << "使用 --help 参数查看命令行格式。" << endl;

  ShuduSolver solver(blockx, blocky);

  char c;
  int val;
  cout << "\n输入初始棋盘，每个方格用一个对应的字符表示，"
       << "空方格用x或0表示：" << endl;
  for (int x = 0; x < size; ++x) {
    for (int y = 0; y < size; ++y) {
      if (!(cin >> c)) exit(-1);
      val = Char2Num(c);
      if (solver.SetCell(x, y, val) == S_FAILED) {
        cout << "\n输入有误或发生冲突：("
             << x+1 << ", " << y+1 << ")不能设置为" << c << endl;
        solver.PrintBoardAll("初始化之后：");
        return -1;
      }
    }
  }
  solver.PrintBoardAll("设置初始数据后得到：");

  cout << "开始推导：" << endl;
  if (!solver.Deduce()) {
    cout << "\n推导失败，初始数据会导致矛盾" << endl;
    solver.PrintBoardAll("推导结果：");
    return -1;
  }

  if (solver.IsOK()) {
    cout << "推导完毕，结果正确。" << endl;
    solver.PrintBoardMark("最后结果：");
    return 0;
  }

  cout << "推导完毕，未能求解。\n" << endl;
  solver.PrintBoardAll("推导结果：");
  if (g_disable_guess) return 0;

  cout << "开始搜索可行解：" << endl;
  solver.SolveDoubt();
  int solutionCnt = solver.GetSolutionCnt();
  if (solutionCnt == 0) {
    cout << "\n此题无解。" << endl;
  } else if (solutionCnt < g_max_solution) {
    cout << "\n搜索完毕，此题共有" << solutionCnt << "个可行解。" << endl;
  } else {
    cout << "\n发现" << solutionCnt << "个可行解，中止搜索。" << endl;
  }

  return 0;
}
