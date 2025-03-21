let DEBUG = true;

let BASE_COLORS = [[0x00, 0xaa, 0xe8], [0xa0, 0x2b, 0x93], [0x4e, 0xa7, 0x2e], [0xeb, 0x11, 0x11], [0x11, 0x60, 0x11], [0x60, 0x11, 0x11]];

function _r2(v: number): number {
    return Math.floor(v * 100) / 100;
}

function _byte_to_2_hex_digits(b: number): string {
    const map = "0123456789abcdef";
    let hex = map[b & 15];
    b = b >>> 4;
    hex = map[b & 15] + hex;
    return hex;
}

function get_color(i: number, mult: number = 1.0): string {
    let c = BASE_COLORS[i % BASE_COLORS.length];
    return '#' + _cc(c[0], mult) + _cc(c[1], mult) + _cc(c[2], mult);
}

function _cc(b: number, mult: number): string {
    if (mult > 1.)
        return _byte_to_2_hex_digits(255 - Math.floor((255 - b) / mult));
    return _byte_to_2_hex_digits(Math.floor(b * mult));
}

function msg(s: string) {
    if (DEBUG)
        console.log(s)
}

function date_from_excel(dateVal: string | number | boolean): Date {
    if (typeof (dateVal) === "number")
        return new Date(Math.round((dateVal - 25569) * 86400 * 1000));
    throw "The date should be a date encoded as a number: " + dateVal.toString();
}

function date_to_string(dateVal: number): string {
    let d = new Date(Math.round((dateVal - 25569) * 86400 * 1000));
    return d.toLocaleDateString();
}

function type_check(t: string, value: number | string | boolean, ref: string = null) {
    if (typeof (value) === t)
        return;
    if (ref)
        throw new Error(`The value in [${ref}] should be of type ${t}, not ${typeof (value)}`)
    throw new Error(`The value [{$value}] should be of type ${t}, not ${typeof (value)}`)
}

function ensure_number(value: number | string | boolean, ref: string = null): number {
    type_check("number", value, ref);
    return value as number;
}

function ensure_boolean(value: number | string | boolean, ref: string = null): boolean {
    type_check("boolean", value, ref);
    return value as boolean;
}


class Config {
    MESSAGE_CELL: string = null;
    RESOURCE_GROUPS: number = null;
    START_DATE_CELL: string = null;
    SPRINT_LENGTH_CELL: string = null;
    INVERTED_WORKDAYS_RANGE: string = null;
    WIDE_SPRINT_TOTAL_ESTIMATES_RANGE: string = null;
    NARROW_SPRINT_TOTAL_ESTIMATES_RANGE: string = null;
    WIDE_SPRINT_REMAINING_ESTIMATES_RANGE: string = null;
    NARROW_SPRINT_REMAINING_ESTIMATES_RANGE: string = null;
    GROUP_NAMES: Array<string> = null;
    GROUP_CODES: Array<string> = null;
    WIDE_SPRINT_BURNDOWN_DATA_RANGE: string = null;
    WIDE_SPRINT_BURNDOWN_HEADER_RANGE: string = null;
    NARROW_SPRINT_BURNDOWN_DATA_RANGE: string = null;
    NARROW_SPRINT_BURNDOWN_HEADER_RANGE: string = null;
    WIDE_DAYS_LEFT_RANGE: string = null;
    NARROW_DAYS_LEFT_RANGE: string = null;
    WIDE_INITIAL_DAYS_RANGE: string = null;
    NARROW_INITIAL_DAYS_RANGE: string = null;
    WIDE_GROUP_NAMES_RANGES: Array<string> = null;
    NARROW_GROUP_NAMES_RANGES: Array<string> = null;
    WIDE_SPRINT_SCOPE_RANGE: string = null;
    NARROW_SPRINT_SCOPE_RANGE: string = null;
    WIDE_ISSUE_REMAINING_ESTIMATES_RANGE: string = null;
    NARROW_ISSUE_REMAINING_ESTIMATES_RANGE: string = null;
    WIDE_POSTPONED_RANGE: string = null;
    NARROW_POSTPONED_RANGE: string = null;
    ISSUE_KEYS_RANGE: string = null;
    SUMMARIES_RANGE: string = null;
    RESOLVED_RANGE: string = null;
    ASSIGNEES_RANGE: string = null;
    PREFIX_RANGE: string = null;
    TODAY_CELL: string = null;
    TODAY_IS: number = null;
    LOCK_CELL: string = null;
    JQL: string = null;
    JIRA_PROXY: string = null;
    ERROR: Error = null;
}


let CONFIG_RANGE = "A1:B40";

function read_config(sheet: ExcelScript.Worksheet): Array<Array<number | string | boolean>> {
    return sheet.getRange(CONFIG_RANGE).getValues();
}


function get_config_value(cfg: Array<Array<number | string | boolean>>, name: string, t: string, array_length: number = null, check: (n: unknown) => boolean = null, chk_msg: string = ""): number | string | boolean | Array<number | string | boolean> {
    for (let i in cfg) {
        //msg(`CFG->${i}:cfg[i][0]:${cfg[i][1]}`)
        let k = (cfg[i][0] as string); //.trim();
        if (k == name) {
            let cell_value = cfg[i][1];
            //msg (`"${name}" found in line ${i}`)
            if (array_length !== null) {
                if (typeof (cell_value) != "string")
                    throw new Error(`Config parameter '${name}': Only strings are supported`);
                let res: Array<number | string | boolean> = cell_value.split(',');
                if (array_length != -1 && res.length != array_length) {
                    throw new Error(`Config parameter '${name}': Array length (${array_length}) differs from actual size(${res.length}`);
                }
                for (let j = 0; j < array_length; j++) {
                    let val = (res[j] as string);
                    if (typeof (val) != t)
                        throw new Error(`Data type for ${name}[${j}] should be ${t} (now ${typeof (val)})`);
                    if (check && !check(val))
                        throw new Error(`Config parameter '${name}[${j}]': ${chk_msg}`);
                }
                return res;
            }
            else {
                let val = cfg[i][1];
                if (typeof (val) != t)
                    throw new Error(`Data type for ${name} should be ${t} (now ${typeof (val)})`);
                if(check && !check(val))
                    throw new Error(`Config parameter '${name}': ${chk_msg}`);
                return val;
            }
        }
    }
    throw new Error(`"${name}" was not found in the config`);
}


function narrow_range(sheet: ExcelScript.Worksheet, range: string, width: number, err: string): string {
    let ir = sheet.getRange(range);
    if(ir.getColumnCount() < width)
        throw new Error(`${err}: the range (${range}) shoud have at least ${width} columns for the given number of resource groups`);
    let mrs = ir.getAbsoluteResizedRange(ir.getRowCount(), width).getAddress(). split('!');
    let res = mrs[mrs.length - 1];
    return res;
}


function getConfig(sheet: ExcelScript.Worksheet): Config {

    // msg(narrow_range(wb, "E13:G32", 2, "Oops!"));

    let cfg_data = read_config(sheet);
    let cfg = new Config();

    /*
    function range_cellcount_is(count: number): (v: unknown) => boolean {
        return (v: unknown) => sheet.getRange(v as string).getCellCount() == count;
    }
    */

    function range_width_is(width: number): (v: unknown) => boolean {
        return (v: unknown) => sheet.getRange(v as string). getWidth() == width;
    }

    cfg.MESSAGE_CELL = get_config_value(cfg_data, "Message cell", "string") as string
    try {
        let rgm = "Range size should correspond to Resource groups";
        let w1m = "The range should have a single column";
        cfg.RESOURCE_GROUPS = get_config_value(cfg_data, "Resource groups", "number") as number;
        cfg.START_DATE_CELL = get_config_value(cfg_data, "Start date cell", "string") as string
        cfg.SPRINT_LENGTH_CELL = get_config_value(cfg_data, "Sprint length cell", "string") as string;
        cfg.INVERTED_WORKDAYS_RANGE = get_config_value(cfg_data, "Inverted workdays range", "string") as string;
        cfg.WIDE_SPRINT_TOTAL_ESTIMATES_RANGE = get_config_value(cfg_data, "Sprint total estimate range", "string") as string;
        cfg.NARROW_SPRINT_TOTAL_ESTIMATES_RANGE = narrow_range(sheet, cfg.WIDE_SPRINT_TOTAL_ESTIMATES_RANGE, cfg.RESOURCE_GROUPS, "Sprint total estimate range");
        cfg.WIDE_SPRINT_REMAINING_ESTIMATES_RANGE = get_config_value(cfg_data, "Sprint remaining estimate range", "string") as string;
        cfg.NARROW_SPRINT_REMAINING_ESTIMATES_RANGE = narrow_range(sheet, cfg.WIDE_SPRINT_REMAINING_ESTIMATES_RANGE, cfg.RESOURCE_GROUPS, "Sprint remaining estimate range");
        cfg.GROUP_NAMES = get_config_value(cfg_data, "Group names", "string", cfg.RESOURCE_GROUPS) as Array<string>;
        cfg.GROUP_CODES = get_config_value(cfg_data, "Group codes", "string", cfg.RESOURCE_GROUPS) as Array<string>;
        cfg.WIDE_SPRINT_BURNDOWN_DATA_RANGE = get_config_value(cfg_data, "Sprint burndown data range", "string") as string;
        cfg.NARROW_SPRINT_BURNDOWN_DATA_RANGE = narrow_range(sheet, cfg.WIDE_SPRINT_BURNDOWN_DATA_RANGE, cfg.RESOURCE_GROUPS * 2 + 2, "Sprint burndown data range")
        cfg.WIDE_SPRINT_BURNDOWN_HEADER_RANGE = get_config_value(cfg_data, "Sprint burndown header range", "string") as string;
        cfg.NARROW_SPRINT_BURNDOWN_HEADER_RANGE = narrow_range(sheet, cfg.WIDE_SPRINT_BURNDOWN_HEADER_RANGE, cfg.RESOURCE_GROUPS * 2 + 2, "Sprint burndown header range")
        cfg.WIDE_DAYS_LEFT_RANGE = get_config_value(cfg_data, "Days left range", "string") as string;
        cfg.NARROW_DAYS_LEFT_RANGE = narrow_range(sheet, cfg.WIDE_DAYS_LEFT_RANGE, cfg.RESOURCE_GROUPS, "Days left range");
        cfg.WIDE_INITIAL_DAYS_RANGE = get_config_value(cfg_data, "Initial days range", "string") as string;
        cfg.NARROW_INITIAL_DAYS_RANGE = narrow_range(sheet, cfg.WIDE_INITIAL_DAYS_RANGE, cfg.RESOURCE_GROUPS, "Initial days range");
        cfg.WIDE_GROUP_NAMES_RANGES = get_config_value(cfg_data, "Group names ranges", "string", -1) as Array<string>;
        cfg.NARROW_GROUP_NAMES_RANGES = [];
        for (let i in cfg.WIDE_GROUP_NAMES_RANGES)
            cfg.NARROW_GROUP_NAMES_RANGES.push(narrow_range(sheet, cfg.WIDE_GROUP_NAMES_RANGES[i], cfg.RESOURCE_GROUPS, "Group names ranges"));
        cfg.WIDE_SPRINT_SCOPE_RANGE = get_config_value(cfg_data, "Sprint scope range", "string") as string;
        cfg.NARROW_SPRINT_SCOPE_RANGE = narrow_range(sheet, cfg.WIDE_SPRINT_SCOPE_RANGE, cfg.RESOURCE_GROUPS, "Sprint scope range");
        cfg.WIDE_ISSUE_REMAINING_ESTIMATES_RANGE = get_config_value(cfg_data, "Issue remaining estimates range", "string") as string;
        cfg.NARROW_ISSUE_REMAINING_ESTIMATES_RANGE = narrow_range(sheet, cfg.WIDE_ISSUE_REMAINING_ESTIMATES_RANGE, cfg.RESOURCE_GROUPS, "Issue remaining estimates range");
        cfg.WIDE_POSTPONED_RANGE = get_config_value(cfg_data, "Postponed range", "string") as string;
        cfg.NARROW_POSTPONED_RANGE = narrow_range(sheet, cfg.WIDE_POSTPONED_RANGE, cfg.RESOURCE_GROUPS, "Postponed range");

        cfg.ISSUE_KEYS_RANGE = get_config_value(cfg_data, "Issue keys range", "string", null, range_width_is(1), w1m) as string;
        cfg.SUMMARIES_RANGE = get_config_value(cfg_data, "Summaries range", "string", null, range_width_is(1), w1m) as string;
        cfg.RESOLVED_RANGE = get_config_value(cfg_data, "Resolved range", "string", null, range_width_is(1), w1m) as string;
        cfg.ASSIGNEES_RANGE = get_config_value(cfg_data, "Assignees range", "string", null, range_width_is(1), w1m) as string;
        cfg.PREFIX_RANGE = get_config_value(cfg_data, "Prefix range", "string", null, range_width_is(1), w1m) as string;
        cfg.TODAY_CELL = get_config_value(cfg_data, "Today cell", "string") as string;
        cfg.TODAY_IS = sheet.getRange(cfg.TODAY_CELL).getCell(0, 0).getValue() as number;
        cfg.LOCK_CELL = get_config_value(cfg_data, "Lock cell", "string") as string;
        cfg.JQL = get_config_value(cfg_data, "JQL", "string") as string;
        cfg.JIRA_PROXY = get_config_value(cfg_data, "Jira proxy", "string") as string;

        if (sheet.getRange(cfg.NARROW_DAYS_LEFT_RANGE).getColumnCount() != cfg.RESOURCE_GROUPS || sheet.getRange(cfg.NARROW_INITIAL_DAYS_RANGE).getColumnCount() != cfg.RESOURCE_GROUPS) {
            throw new Error("Number of columns in 'Days left range' and 'Initial days range' should be equal to the current value of 'Resource groups' which is " + cfg.RESOURCE_GROUPS);
        }
        if (sheet.getRange(cfg.NARROW_DAYS_LEFT_RANGE).getRowCount() != 1 || sheet.getRange(cfg.NARROW_INITIAL_DAYS_RANGE).getRowCount() != 1) {
            throw new Error("Number of rows in 'Days left range' and 'Initial days range' should be 1");
        }

        let out = "################## Configuration ##################";
        for(let f in cfg) {
            out += `\n${f}: ${cfg[f]}`;
        }
        out += "\n###################################################";
        msg(out);
    } catch (e) {
        if (!(e instanceof Error))
            throw e;
        cfg.ERROR = e;
    }
    return cfg;
}


function isWorkingDay(idate: number, inverted: Array<number>): boolean {
    let wd = date_from_excel(idate).getDay();
    let invert = false;
    let weekend = wd == 0 || wd == 6;
    inverted.forEach((v) => invert = (invert || idate == v));
    return weekend === invert;
}


function linearise<T>(arr: T): Array<number | string | boolean> {
    let res: Array<number | string | boolean> = [];
    if (arr instanceof Array)
        for (let i in arr)
            linearise(arr[i]).forEach((v) => res.push(v))
    else
        if(!(typeof(arr) == "string" && arr as string == ""))
            res.push((arr as unknown as (number | string | boolean)))
    return res;
}


function result(ok: boolean, wb: ExcelScript.Workbook, cfg: Config, message: string) {
    let sheet = wb.getActiveWorksheet();
    let cell = sheet.getRange(cfg.MESSAGE_CELL).getCell(0, 0);
    if (ok)
        cell.setPredefinedCellStyle("Good");
    else
        cell.setPredefinedCellStyle("Bad");
    cell.setValue(message);
}


function in_progress(wb: ExcelScript.Workbook, cfg: Config, message: string) {
    let sheet = wb.getActiveWorksheet();
    let cell = sheet.getRange(cfg.MESSAGE_CELL).getCell(0, 0);
    cell.setPredefinedCellStyle("Neutral");
    cell.setValue(message);
}


function update(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    let lk = ensure_boolean(sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).getValue(), cfg.LOCK_CELL);
    if (!lk)
        throw new Error("You should lock the data (fix the sprint scope) to run UPDATE");
    let today = cfg.TODAY_IS;
    let sprint_len = (sheet.getRange(cfg.SPRINT_LENGTH_CELL).getValue());

    let burndown_data_range = sheet.getRange(cfg.NARROW_SPRINT_BURNDOWN_DATA_RANGE);
    let burndown_data = burndown_data_range.getValues();

    let day_idx: number = null;
    for (let i = 0; i < burndown_data.length; i++)
        if (burndown_data[i][1] == today) {
            day_idx = i;
            break
        }
    if (day_idx === null)
        throw Error(`The current date (${date_to_string(today)}) is not found in the sprint burndown graph`);

    let curr_values = 0;
    let current_estimates = (linearise(sheet.getRange(cfg.NARROW_SPRINT_REMAINING_ESTIMATES_RANGE).getValues()) as Array<number>);
    for (let i in current_estimates)
        ensure_number(current_estimates[i], `SPRINT_REMAINING_ESTIMATES_RANGE[${i}]`)

    for (let i = 0; i < cfg.RESOURCE_GROUPS; i++)
        burndown_data[day_idx][2 + cfg.RESOURCE_GROUPS + i] = current_estimates[i];
    burndown_data_range.setValues(burndown_data);
    result(true, wb, cfg, "The UPDATE was successful!")
}


function lock(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    sheet.getRange(cfg.NARROW_SPRINT_SCOPE_RANGE).setPredefinedCellStyle("Explanatory text");
    sheet.getRange(cfg.NARROW_POSTPONED_RANGE).setPredefinedCellStyle("Explanatory text");
    sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).setValue(true);
    sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).setPredefinedCellStyle("Bad");
    result(true, wb, cfg, "Data locked");
}


function unlock(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    sheet.getRange(cfg.NARROW_SPRINT_SCOPE_RANGE).setPredefinedCellStyle("Normal");
    sheet.getRange(cfg.NARROW_POSTPONED_RANGE).setPredefinedCellStyle("Normal");
    sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).setValue(false);
    sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).setPredefinedCellStyle("Normal");
    result(true, wb, cfg, "Data unlocked");
}


function recalc(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    let lk = ensure_boolean(sheet.getRange(cfg.LOCK_CELL).getCell(0, 0).getValue(), cfg.LOCK_CELL);
    if (lk)
        throw new Error("Data is locked, unlock to be able to RECALC!");

    let sprint_len = (sheet.getRange(cfg.SPRINT_LENGTH_CELL).getValue());
    let total_estimates: Array<number> = [];
    linearise(sheet.getRange(cfg.NARROW_SPRINT_TOTAL_ESTIMATES_RANGE).getValues()).forEach(
        (v) => (total_estimates.push((v as number)))
    );

    //let inverted_range = linearise(selectedSheet.getRange(cfg.INVERTED_WORKDAYS_RANGE).getValues());
    let inverted_days: Array<number | string | boolean> = (linearise(sheet.getRange(cfg.INVERTED_WORKDAYS_RANGE).getValues()) as Array<number | string | boolean>);

    let numDays = ensure_number(sheet.getRange(cfg.SPRINT_LENGTH_CELL).getValue(), cfg.SPRINT_LENGTH_CELL);
    let totalEstimates = (linearise(sheet.getRange(cfg.NARROW_SPRINT_TOTAL_ESTIMATES_RANGE).getValues()) as Array<number>);
    for (let i in totalEstimates)
        ensure_number(totalEstimates[i], `SPRINT_TOTAL_ESTIMATES_RANGE[${i}]`)
    let startDate = ensure_number(sheet.getRange(cfg.START_DATE_CELL).getValue(), cfg.START_DATE_CELL);

    let burndown_data_range = sheet.getRange(cfg.NARROW_SPRINT_BURNDOWN_DATA_RANGE);
    let burndown_data = burndown_data_range.getValues();
    let data_column_count = burndown_data_range.getColumnCount();
    let data_row_count = burndown_data_range.getRowCount();
    for (let c = 0; c < data_column_count; c++)
        for (let r = 0; r < data_row_count; r++)
            if (c < 2 + cfg.RESOURCE_GROUPS)
                burndown_data[r][c] = "";
    burndown_data_range.setValues(burndown_data);
    burndown_data = burndown_data_range.getValues();
    let currDate = startDate;
    for (let day = 0; day <= numDays; day++) {
        while (!isWorkingDay(currDate, (inverted_days as Array<number>)))
            currDate++;
        burndown_data[day][0] = day + 1;
        burndown_data[day][1] = date_to_string(currDate);
        for (let rg = 0; rg < cfg.RESOURCE_GROUPS; rg++) {
            burndown_data[day][2 + rg] = _r2(totalEstimates[rg] * (1. - day / numDays));
        }
        currDate++;
    }
    burndown_data_range.setValues(burndown_data);

    let charts = sheet.getCharts();
    let lineChart: ExcelScript.Chart = null;
    for (let c in charts) {
        if (charts[c].getTitle().getText() == "Burndown") {
            lineChart = charts[c];
        }
    }

    let left_top = burndown_data_range.getCell(0, 0).getAddress();
    let right_bottom = burndown_data_range.getCell(numDays, 1 + 2 * cfg.RESOURCE_GROUPS).getAddress();
    let table_range_str = left_top + ":" + right_bottom;
    if (lineChart === null)
        lineChart = sheet.addChart(ExcelScript.ChartType.lineMarkers, sheet.getRange(table_range_str), ExcelScript.ChartSeriesBy.columns);
    else
        lineChart.setData(sheet.getRange(table_range_str));
    lineChart.getTitle().setText("Burndown");
    let series = lineChart.getSeries();

    for (let rg = 0; rg < cfg.RESOURCE_GROUPS; rg++) {
        let bs = series[rg + cfg.RESOURCE_GROUPS];
        let ps = series[rg]
        bs.setName(cfg.GROUP_NAMES[rg]);
        ps.setName(cfg.GROUP_NAMES[rg] + ", plan");
        let main_format = series[rg + cfg.RESOURCE_GROUPS].getFormat();
        let main_line = main_format.getLine();
        let planned_line = series[rg].getFormat().getLine();
        main_line.setColor(get_color(rg, 1.0));
        planned_line.setColor(get_color(rg, 2.9));
        planned_line.setLineStyle(ExcelScript.ChartLineStyle.dot);
        planned_line.setWeight(1);
        bs.setMarkerForegroundColor(get_color(rg, 0.7));
        ps.setMarkerStyle(ExcelScript.ChartMarkerStyle.none);
        bs.setMarkerBackgroundColor(get_color(rg, 1.2));
    }

    let days_left_range = sheet.getRange(cfg.NARROW_DAYS_LEFT_RANGE);

    let barChart: ExcelScript.Chart = null;

    for (let c in charts) {
        if (charts[c].getTitle().getText() == "Days Left") {
            barChart = charts[c];
        }
    }

    if (barChart === null)
        barChart = sheet.addChart(ExcelScript.ChartType.barStacked, days_left_range);
    else {
        barChart.setData(days_left_range);
    }
    barChart.getSeries()[0].setXAxisValues(sheet.getRange(cfg.NARROW_GROUP_NAMES_RANGES[0]));
    barChart.getTitle().setText("Days Left");

    lock(wb, cfg);
}


async function sendPostRequest(url: string, data: unknown): Promise<unknown> {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseData: unknown = await response.json();
        return responseData;
    } catch (error) {
        console.log('Error:', error);
        return null;
    }
}


function read_range(sheet: ExcelScript.Worksheet, range: string): Array<Array<number | string | boolean>> {
  return sheet.getRange(range).getValues();
}

function clear_cells(arr: Array<Array<number | string | boolean>>): Array<Array<number | string | boolean>> {
    for(let skey in arr)
        for(let ckey in arr[skey])
            arr[skey][ckey] = "";
    return arr;
}

function find_index(codes: Array<string>, val: string): number {
    for(let i=0; i < codes.length; i++)
        if(codes[i] == val)
            return i;
    return null;
}

function groups(row: Array<number | string | boolean>, cfg: Config, estimates: Object) {
    for(let k in estimates) {
        let i = find_index(cfg.GROUP_CODES, k);
        if(i!=null)
            if(estimates[k])
                row[i] = +estimates[k];
            else
                row[i] = '';
    }
}


async function from_jira(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();

    let summaries = clear_cells(sheet.getRange(cfg.SUMMARIES_RANGE).getValues());
    let keys = clear_cells(sheet.getRange(cfg.ISSUE_KEYS_RANGE).getValues());
    let scope = clear_cells(sheet.getRange(cfg.NARROW_SPRINT_SCOPE_RANGE).getValues());
    let remaining = clear_cells(sheet.getRange(cfg.NARROW_ISSUE_REMAINING_ESTIMATES_RANGE).getValues());
    let prefixes = clear_cells(sheet.getRange(cfg.PREFIX_RANGE).getValues());
    let resolved = clear_cells(sheet.getRange(cfg.RESOLVED_RANGE).getValues());
    let assignee = clear_cells(sheet.getRange(cfg.ASSIGNEES_RANGE).getValues());
    let data = {
        'jql': cfg.JQL,
        'resource_groups': cfg.GROUP_CODES,
    };
    let res: Object = await sendPostRequest(cfg.JIRA_PROXY + '/query_issues', data) as Object;
    if(res) {
        for(let k=0; k < res["issues"].length; k++) {
            let issue = res["issues"][k] as Object;
            //sort_values[k][0] =
            keys[k][0] = issue["key"] as string;
            prefixes[k][0] = issue["prefix"] as string;
            summaries[k][0] = issue["summary"] as string;
            resolved[k][0] = issue["resolution"] ? "+": "";
            assignee[k][0] = issue["assignee"] as string;
            groups(scope[k], cfg, issue["estimates"]);
            groups(remaining[k], cfg, issue["remaining_estimates"]);
        }
        sheet.getRange(cfg.SUMMARIES_RANGE).setValues(summaries);
        sheet.getRange(cfg.ISSUE_KEYS_RANGE).setValues(keys);
        sheet.getRange(cfg.NARROW_SPRINT_SCOPE_RANGE).setValues(scope);
        sheet.getRange(cfg.NARROW_ISSUE_REMAINING_ESTIMATES_RANGE).setValues(remaining);
        sheet.getRange(cfg.PREFIX_RANGE).setValues(prefixes);
        sheet.getRange(cfg.RESOLVED_RANGE).setValues(resolved);
        sheet.getRange(cfg.ASSIGNEES_RANGE).setValues(assignee);
        result(true, wb, cfg, "Jira import: done.");
    } else
        result(false, wb, cfg, "Jira import: failed to get data.");
}

function gather_estimates(estimates: Array<number | string | boolean>, cfg: Config): Object {
    let res = {};
    for (let i in estimates) {
        let ii = +i;
        if (estimates[ii] != '')
            if (ii < cfg.GROUP_CODES.length)
                res[cfg.GROUP_CODES[ii]] = estimates[ii];
    }
    return res;
}

async function to_jira(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();

    //let sort_values = sheet.getRange(cfg.SORT_KEYS_RANGE).getValues();
    let summaries = sheet.getRange(cfg.SUMMARIES_RANGE).getValues();
    let keys = sheet.getRange(cfg.ISSUE_KEYS_RANGE).getValues();
    let scope = sheet.getRange(cfg.NARROW_SPRINT_SCOPE_RANGE).getValues();
    let remaining = sheet.getRange(cfg.NARROW_ISSUE_REMAINING_ESTIMATES_RANGE).getValues();
    let prefixes = sheet.getRange(cfg.PREFIX_RANGE).getValues();
    let resolved = sheet.getRange(cfg.RESOLVED_RANGE).getValues();

    let issues: Array<Object> = [];
    //msg(`KEYS ${keys.length}:${keys[0][0]}`);
    for( let i=0; i < keys.length && keys[i][0].toString() != ""; i++) {
        //msg(`${keys[i][0]}: `);
        let e = gather_estimates(scope[i], cfg);
        let re = gather_estimates(remaining[i], cfg);
        let prefix = prefixes[i][0] as string;
        if(prefix.length > 3)
            prefix = prefix.substring(0,3);
        issues.push({
            key: keys[i][0],
            estimates: e,
            remaining_estimates: re,
            summary: summaries[i][0],
            prefix: prefix
        });
    }
    let data = {
        'jql': cfg.JQL,
        'issues': issues,
    };
    let res: Object = await sendPostRequest(cfg.JIRA_PROXY + '/update_issues', data) as Object;
    result(true, wb, cfg, `Updated: ${res["updated_keys"]}`);
}

function fill_range(sheet: ExcelScript.Worksheet, range: string, row: Array<string>) {
    let r = sheet.getRange(range);
    let matrix: Array<Array<string>> = new Array(r.getRowCount()).fill(row);
    r.setValues(matrix);
}

function clear_range(sheet:ExcelScript.Worksheet, range: string) {
    let r = sheet.getRange(range);
    fill_range(sheet, range, new Array(r.getColumnCount()).fill(""));
}

function setup(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    for (let i in cfg.WIDE_GROUP_NAMES_RANGES)
        clear_range(sheet, cfg.WIDE_GROUP_NAMES_RANGES[i]);
    for(let i in cfg.NARROW_GROUP_NAMES_RANGES)
        fill_range(sheet, cfg.NARROW_GROUP_NAMES_RANGES[i], cfg.GROUP_NAMES);
    clear_range(sheet, cfg.WIDE_SPRINT_BURNDOWN_HEADER_RANGE);
    let bth_hdr = ["#", "Date"];
    for(let i in cfg.GROUP_CODES)
        bth_hdr.push(cfg.GROUP_CODES[i]+", plan")
    for (let i in cfg.GROUP_CODES)
        bth_hdr.push(cfg.GROUP_CODES[i]);
    sheet.getRange(cfg.NARROW_SPRINT_BURNDOWN_HEADER_RANGE).setValues([bth_hdr]);

    let ranges = [sheet.getRange(cfg.WIDE_SPRINT_SCOPE_RANGE), sheet.getRange(cfg.WIDE_ISSUE_REMAINING_ESTIMATES_RANGE), sheet.getRange(cfg.WIDE_POSTPONED_RANGE)];
    let width = 0;
    for(let i=0; i < ranges.length; i++){
        let range = sheet.getRange(cfg.WIDE_GROUP_NAMES_RANGES[i]);
        let nrange_size = sheet.getRange(cfg.NARROW_GROUP_NAMES_RANGES[i]).getColumnCount();
        if(i != 0)
            range.getCell(0, -1).getFormat().setColumnWidth(0);
        let cols = range.getColumnCount();
        for(let j=0; j < cols; j++) {
            let gname_cell = range.getCell(0, j);
            let focus_cell = gname_cell.getCell(1, 0);
            let mul_cell = gname_cell.getCell(2, 0);
            let sp_cell = gname_cell.getCell(3, 0);
            let days_cell = gname_cell.getCell(4, 0);
            if (j == 0 && i == 0)
                width = gname_cell.getFormat().getColumnWidth();
            if (j < nrange_size) {
                sp_cell.setFormula(`=SUM(${ranges[i].getColumn(j).getAddressLocal()})`);
                days_cell.setFormula(`=(${sp_cell.getAddressLocal()}*${mul_cell.getAddressLocal()}/${focus_cell.getAddressLocal()})`);
                let mv = mul_cell.getValue();
                if (typeof (mv) == "string" && mv == "")
                    mul_cell.setValue(1.5);
                let fv = focus_cell.getValue();
                if (typeof (fv) == "string" && fv == "")
                    focus_cell.setValue(8);
                sp_cell.getFormat().setColumnWidth(width);
            } else {
                sp_cell.setFormula("");
                days_cell.setFormula("");
                sp_cell.getFormat().setColumnWidth(0);
            }
        }
    }
    result(true, wb, cfg, `Configured for ${cfg.RESOURCE_GROUPS} groups\nCodes: ${cfg.GROUP_CODES}\nNames: ${cfg.GROUP_NAMES}`);
}

function apply(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    sheet.getRange("A1").getFormat().setColumnWidth(0);
    sheet.getRange("B1").getFormat().setColumnWidth(0);
    setup(wb, cfg);
}

function config(wb: ExcelScript.Workbook, cfg: Config) {
    let sheet = wb.getActiveWorksheet();
    sheet.getRange("A1").getFormat().setColumnWidth(250);
    sheet.getRange("B1").getFormat().setColumnWidth(250);
    result(true, wb, cfg, `Please edit the config and run "APPLY"`);
}


const CELL_MESSAGE = "Please select an action by selecting an action cell (RECALC/UPDATE/LOCK/UNLOCK/FROM JIRA/TO JIRA/SETUP/TEST/CONFIG/APPLY)";

async function main(wb: ExcelScript.Workbook) {
    var cfg = getConfig(wb.getActiveWorksheet());
    try {
        if (cfg.ERROR)
            throw cfg.ERROR;
        let v = wb.getActiveCell().getValue();

        in_progress(wb, cfg, `Running action ${v}`)

        if (v === null)
            throw new Error(CELL_MESSAGE);
        let action = (v as string);
        if (action === "RECALC")
            recalc(wb, cfg);
        else if (action === "UPDATE")
            update(wb, cfg);
        else if (action === "LOCK")
            lock(wb, cfg);
        else if (action === "UNLOCK")
            unlock(wb, cfg);
        else if (action === "FROM JIRA")
            await from_jira(wb, cfg);
        else if (action === "TO JIRA")
            await to_jira(wb, cfg);
        else if (action === "CONFIG")
            config(wb, cfg);
        else if (action === "APPLY")
            apply(wb, cfg);
        else
            throw new Error(CELL_MESSAGE);
    } catch (e) {
        result(false, wb, cfg, e.message);
    }
}
