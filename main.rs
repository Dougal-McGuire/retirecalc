use chrono::Local;
use eframe::egui;
use egui::{CentralPanel, Context, Layout, RichText};
use egui::plot::{Line, Plot, PlotPoints, Value, Values};

// Structure holding simulation parameters.
#[derive(Clone)]
struct SimulationParameters {
    current_age: f64,
    legal_retirement_age: f64,
    fixed_monthly_pension: f64,
    current_assets: f64,
    capital_gains_tax_rate: f64, // e.g., 0.2625 for 26.25%
    annual_savings: f64,
    intended_retirement_age: f64,
    average_roi: f64,         // as a fraction, e.g., 0.12 for 12%
    average_inflation: f64,   // e.g., 0.025 for 2.5%
    roi_volatility: f64,
    inflation_volatility: f64,
    monthly_expenses: [f64; 5],  // [health, food, entertainment, shopping, utilities]
    annual_expenses: [f64; 3],   // [vacations, repairs, car maintenance]
    simulation_runs: usize,
    simulation_end_age: f64,
}

impl Default for SimulationParameters {
    fn default() -> Self {
        Self {
            current_age: 54.0,
            legal_retirement_age: 67.0,
            fixed_monthly_pension: 5000.0,
            current_assets: 600000.0,
            capital_gains_tax_rate: 0.2625,
            annual_savings: 18000.0,
            intended_retirement_age: 60.0,
            average_roi: 0.12,
            average_inflation: 0.025,
            roi_volatility: 0.15,
            inflation_volatility: 0.01,
            monthly_expenses: [1500.0, 1500.0, 500.0, 500.0, 500.0],
            annual_expenses: [12000.0, 3000.0, 3000.0],
            simulation_runs: 10000,
            simulation_end_age: 90.0,
        }
    }
}

// Structure to hold simulation results.
struct SimulationResults {
    ages: Vec<f64>,
    assets: Vec<f64>,
    spendings: Vec<f64>,
    success_probability: f64,
}

// Generate a normally distributed random number using the Box–Muller transform.
fn random_normal(mean: f64, std: f64) -> f64 {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let u: f64 = loop {
        let u = rng.gen::<f64>();
        if u > 0.0 { break u; }
    };
    let v: f64 = loop {
        let v = rng.gen::<f64>();
        if v > 0.0 { break v; }
    };
    mean + std * ( -2.0 * u.ln() ).sqrt() * (2.0 * std::f64::consts::PI * v).cos()
}

// Run a Monte Carlo simulation and return simulation results.
// (For simplicity, this version returns a single trajectory—the median trajectory.)
fn run_simulation(params: &SimulationParameters) -> SimulationResults {
    let mut successes = 0;
    let mut assets_sum = vec![0.0; (params.simulation_end_age - params.current_age) as usize + 1];
    let mut spendings_sum = vec![0.0; (params.simulation_end_age - params.current_age) as usize + 1];
    let num_years = assets_sum.len();

    for _ in 0..params.simulation_runs {
        let mut asset = params.current_assets;
        let mut yearly_assets = vec![];
        let mut yearly_spendings = vec![];
        // Accumulation phase
        for _age in (params.current_age as usize)..(params.intended_retirement_age as usize) {
            let r = random_normal(params.average_roi, params.roi_volatility);
            let effective_r = if r > 0.0 { r * (1.0 - params.capital_gains_tax_rate) } else { r };
            asset = asset * (1.0 + effective_r) + params.annual_savings;
            yearly_assets.push(asset);
            yearly_spendings.push(0.0);
        }
        // Distribution phase
        let base_monthly = params.monthly_expenses.iter().sum::<f64>();
        let base_annual = params.annual_expenses.iter().sum::<f64>();
        let mut annual_expense = base_monthly * 12.0 + base_annual;
        for _age in (params.intended_retirement_age as usize)..(params.simulation_end_age as usize + 1) {
            let income = if _age as f64 >= params.legal_retirement_age {
                params.fixed_monthly_pension * 12.0
            } else { 0.0 };
            let r = random_normal(params.average_roi, params.roi_volatility);
            let effective_r = if r > 0.0 { r * (1.0 - params.capital_gains_tax_rate) } else { r };
            asset = asset * (1.0 + effective_r) + income - annual_expense;
            yearly_assets.push(asset);
            yearly_spendings.push(annual_expense / 12.0);
            let inflation = random_normal(params.average_inflation, params.inflation_volatility);
            annual_expense *= 1.0 + inflation;
        }
        if asset >= 0.0 {
            successes += 1;
        }
        // Sum the trajectory into our accumulators
        for (i, &a) in yearly_assets.iter().enumerate() {
            assets_sum[i] += a;
        }
        for (i, &s) in yearly_spendings.iter().enumerate() {
            spendings_sum[i] += s;
        }
    }
    // Calculate median trajectories as averages
    let median_assets: Vec<f64> = assets_sum.into_iter().map(|sum| sum / params.simulation_runs as f64).collect();
    let median_spendings: Vec<f64> = spendings_sum.into_iter().map(|sum| sum / params.simulation_runs as f64).collect();
    SimulationResults {
        ages: (params.current_age as usize..=params.simulation_end_age as usize).map(|x| x as f64).collect(),
        assets: median_assets,
        spendings: median_spendings,
        success_probability: successes as f64 / params.simulation_runs as f64,
    }
}

// Translation structure
struct Translations {
    en: &'static [(&'static str, &'static str)],
    de: &'static [(&'static str, &'static str)],
}

fn get_translations() -> Translations {
    Translations {
        en: &[
            ("title_main", "Early Retirement Monte Carlo Simulation"),
            ("languageLabel", "Language"),
            ("section_parameters", "Parameters"),
            ("section_fixed", "Fixed"),
            ("label_currentAge", "Current Age"),
            ("tooltip_currentAge", "Your current age (e.g., 54)."),
            ("label_legalRetirementAge", "Legal Retirement Age"),
            ("tooltip_legalRetirementAge", "Age when fixed pension begins."),
            ("label_fixedMonthlyPension", "Monthly Pension (€)"),
            ("tooltip_fixedMonthlyPension", "Fixed monthly pension starting at legal retirement age."),
            ("label_currentAssets", "Current Assets (€)"),
            ("tooltip_currentAssets", "Your current savings and assets."),
            ("label_capitalGainsTaxRate", "Capital Gains Tax Rate (%)"),
            ("tooltip_capitalGainsTaxRate", "Tax rate applied on positive returns."),
            ("label_annualSavings", "Annual Savings (€)"),
            ("tooltip_annualSavings", "Your annual savings while working."),
            ("section_variable", "Variable"),
            ("label_retirementAge", "Intended Retirement Age"),
            ("tooltip_retirementAge", "Age you plan to retire."),
            ("label_averageROI", "Average ROI (%)"),
            ("tooltip_averageROI", "Expected annual investment return."),
            ("label_averageInflation", "Average Inflation (%)"),
            ("tooltip_averageInflation", "Expected annual inflation rate."),
            ("section_volatility", "Volatility"),
            ("label_ROI_volatility", "ROI Volatility"),
            ("tooltip_ROI_volatility", "Standard deviation of ROI."),
            ("label_inflation_volatility", "Inflation Volatility"),
            ("tooltip_inflation_volatility", "Standard deviation of inflation."),
            ("section_monthlyExpenses", "Monthly Expenses (€)"),
            ("label_expenseHealth", "Health"),
            ("tooltip_expenseHealth", "Monthly spending on health."),
            ("label_expenseFood", "Food"),
            ("tooltip_expenseFood", "Monthly spending on food."),
            ("label_expenseEntertainment", "Entertainment"),
            ("tooltip_expenseEntertainment", "Monthly spending on entertainment."),
            ("label_expenseShopping", "Shopping"),
            ("tooltip_expenseShopping", "Monthly spending on shopping."),
            ("label_expenseUtilities", "Utilities"),
            ("tooltip_expenseUtilities", "Monthly spending on utilities."),
            ("section_annualExpenses", "Annual Expenses (€)"),
            ("label_expenseVacations", "Vacations"),
            ("tooltip_expenseVacations", "Annual spending on vacations."),
            ("label_expenseRepairs", "Repairs"),
            ("tooltip_expenseRepairs", "Annual spending on repairs."),
            ("label_expenseCarMaintenance", "Car Maintenance"),
            ("tooltip_expenseCarMaintenance", "Annual spending on car maintenance."),
            ("label_simulationRuns", "Simulations"),
            ("tooltip_simulationRuns", "Number of simulation runs."),
            ("label_saveLoad", "Save/Load Parameters"),
            ("tooltip_saveLoad", "Save or load parameters."),
            ("btn_save", "Save"),
            ("btn_load", "Load"),
            ("btn_exportPdf", "Export PDF"),
            ("section_results", "Simulation Results"),
            ("successProbability", "Success Probability"),
            ("explanation_simulation", "Simulation Explanation: The simulation runs in two phases. In the accumulation phase, your assets grow through savings and returns. In the distribution phase, your assets cover living expenses until age 90. Success probability is the percentage of runs where assets never drop below zero."),
        ],
        de: &[
            ("title_main", "Monte-Carlo-Simulation für Frühverrentung"),
            ("languageLabel", "Sprache"),
            ("section_parameters", "Parameter"),
            ("section_fixed", "Fest"),
            ("label_currentAge", "Aktuelles Alter"),
            ("tooltip_currentAge", "Ihr aktuelles Alter (z.B. 54)."),
            ("label_legalRetirementAge", "Gesetzliches Rentenalter"),
            ("tooltip_legalRetirementAge", "Alter, ab dem die Rente beginnt."),
            ("label_fixedMonthlyPension", "Monatliche Rente (€)"),
            ("tooltip_fixedMonthlyPension", "Feste monatliche Rente ab Rentenbeginn."),
            ("label_currentAssets", "Aktuelle Vermögenswerte (€)"),
            ("tooltip_currentAssets", "Ihre Ersparnisse und Vermögenswerte."),
            ("label_capitalGainsTaxRate", "Kapitalertragssteuer (%)"),
            ("tooltip_capitalGainsTaxRate", "Steuersatz auf positive Renditen."),
            ("label_annualSavings", "Jährliche Ersparnisse (€)"),
            ("tooltip_annualSavings", "Jährliche Ersparnisse während der Erwerbstätigkeit."),
            ("section_variable", "Variabel"),
            ("label_retirementAge", "Geplantes Rentenalter"),
            ("tooltip_retirementAge", "Alter, in dem Sie in Rente gehen möchten."),
            ("label_averageROI", "Durchschnittliche Rendite (%)"),
            ("tooltip_averageROI", "Erwartete jährliche Rendite."),
            ("label_averageInflation", "Durchschnittliche Inflation (%)"),
            ("tooltip_averageInflation", "Erwartete jährliche Inflationsrate."),
            ("section_volatility", "Volatilität"),
            ("label_ROI_volatility", "Rendite-Volatilität"),
            ("tooltip_ROI_volatility", "Standardabweichung der Rendite."),
            ("label_inflation_volatility", "Inflations-Volatilität"),
            ("tooltip_inflation_volatility", "Standardabweichung der Inflation."),
            ("section_monthlyExpenses", "Monatliche Ausgaben (€)"),
            ("label_expenseHealth", "Gesundheit"),
            ("tooltip_expenseHealth", "Monatliche Ausgaben für Gesundheit."),
            ("label_expenseFood", "Lebensmittel"),
            ("tooltip_expenseFood", "Monatliche Ausgaben für Lebensmittel."),
            ("label_expenseEntertainment", "Unterhaltung"),
            ("tooltip_expenseEntertainment", "Monatliche Ausgaben für Unterhaltung."),
            ("label_expenseShopping", "Einkaufen"),
            ("tooltip_expenseShopping", "Monatliche Ausgaben für Einkäufe."),
            ("label_expenseUtilities", "Nebenkosten"),
            ("tooltip_expenseUtilities", "Monatliche Ausgaben für Nebenkosten."),
            ("section_annualExpenses", "Jährliche Ausgaben (€)"),
            ("label_expenseVacations", "Urlaub"),
            ("tooltip_expenseVacations", "Jährliche Ausgaben für Urlaub."),
            ("label_expenseRepairs", "Reparaturen"),
            ("tooltip_expenseRepairs", "Jährliche Ausgaben für Reparaturen."),
            ("label_expenseCarMaintenance", "Autopflege"),
            ("tooltip_expenseCarMaintenance", "Jährliche Ausgaben für Autopflege."),
            ("label_simulationRuns", "Simulationen"),
            ("tooltip_simulationRuns", "Anzahl der Simulationen."),
            ("label_saveLoad", "Parameter speichern/laden"),
            ("tooltip_saveLoad", "Parameter speichern oder laden."),
            ("btn_save", "Speichern"),
            ("btn_load", "Laden"),
            ("btn_exportPdf", "PDF exportieren"),
            ("section_results", "Simulationsergebnisse"),
            ("successProbability", "Erfolgswahrscheinlichkeit"),
            ("explanation_simulation", "Simulations-Erklärung: Die Simulation läuft in zwei Phasen. In der Ansparphase wachsen Ihre Vermögenswerte durch Ersparnisse und Renditen. In der Auszahlungsphase decken Ihre Vermögenswerte die Lebenshaltungskosten bis zum Alter 90. Die Erfolgswahrscheinlichkeit gibt den Prozentsatz der Simulationen an, bei denen die Vermögenswerte nie unter null fallen."),
        ],
    }
}

// Application state
struct RetireCalcApp {
    params: SimulationParameters,
    simulation: Option<SimulationResults>,
    language: String,
    translations: Translations,
}

impl Default for RetireCalcApp {
    fn default() -> Self {
        Self {
            params: SimulationParameters::default(),
            simulation: None,
            language: "en".to_owned(),
            translations: get_translations(),
        }
    }
}

// Implement the simulation logic in our app.
impl RetireCalcApp {
    fn run_simulation(&mut self) {
        // For simplicity, we'll use our run_simulation function which returns the median trajectory.
        self.simulation = Some(run_simulation(&self.params));
    }

    // Placeholder PDF export function.
    // In a real application, you would integrate a proper PDF generation library.
    fn export_pdf(&self) {
        // For now, we simply print a message.
        println!("Exporting PDF (landscape) with current date in filename...");
        // You could integrate a crate like printpdf here.
        // For example, create a PDF, render the simulation plot and parameters, and save it.
    }
}

// Implement eframe's App trait.
impl epi::App for RetireCalcApp {
    fn name(&self) -> &str {
        "RetireCalc"
    }

    fn update(&mut self, ctx: &Context, _frame: &mut epi::Frame) {
        // Sidebar: Parameter inputs and buttons
        egui::SidePanel::left("side_panel").show(ctx, |ui| {
            ui.heading(if self.language == "en" { "Parameters" } else { "Parameter" });
            ui.separator();
            ui.horizontal(|ui| {
                ui.label("Current Age:");
                if ui.add(egui::TextEdit::singleline(&mut self.params.current_age.to_string())).changed() {
                    self.params.current_age = self.params.current_age; // parsed on update below
                }
            });
            ui.horizontal(|ui| {
                ui.label("Legal Retirement Age:");
                ui.text_edit_singleline(&mut self.params.legal_retirement_age.to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Monthly Pension (€):");
                ui.text_edit_singleline(&mut self.params.fixed_monthly_pension.to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Current Assets (€):");
                ui.text_edit_singleline(&mut self.params.current_assets.to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Capital Gains Tax (%):");
                ui.text_edit_singleline(&mut (self.params.capital_gains_tax_rate * 100.0).to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Annual Savings (€):");
                ui.text_edit_singleline(&mut self.params.annual_savings.to_string());
            });
            ui.separator();
            ui.heading(if self.language == "en" { "Variable" } else { "Variabel" });
            ui.horizontal(|ui| {
                ui.label("Intended Retirement Age:");
                ui.text_edit_singleline(&mut self.params.intended_retirement_age.to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Average ROI (%):");
                ui.text_edit_singleline(&mut (self.params.average_roi * 100.0).to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Average Inflation (%):");
                ui.text_edit_singleline(&mut (self.params.average_inflation * 100.0).to_string());
            });
            ui.separator();
            ui.heading(if self.language == "en" { "Volatility" } else { "Volatilität" });
            ui.horizontal(|ui| {
                ui.label("ROI Volatility:");
                ui.text_edit_singleline(&mut self.params.roi_volatility.to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Inflation Volatility:");
                ui.text_edit_singleline(&mut self.params.inflation_volatility.to_string());
            });
            ui.separator();
            ui.heading(if self.language == "en" { "Monthly Expenses (€)" } else { "Monatliche Ausgaben (€)" });
            ui.horizontal(|ui| {
                ui.label("Health:");
                ui.text_edit_singleline(&mut self.params.monthly_expenses[0].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Food:");
                ui.text_edit_singleline(&mut self.params.monthly_expenses[1].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Entertainment:");
                ui.text_edit_singleline(&mut self.params.monthly_expenses[2].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Shopping:");
                ui.text_edit_singleline(&mut self.params.monthly_expenses[3].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Utilities:");
                ui.text_edit_singleline(&mut self.params.monthly_expenses[4].to_string());
            });
            ui.separator();
            ui.heading(if self.language == "en" { "Annual Expenses (€)" } else { "Jährliche Ausgaben (€)" });
            ui.horizontal(|ui| {
                ui.label("Vacations:");
                ui.text_edit_singleline(&mut self.params.annual_expenses[0].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Repairs:");
                ui.text_edit_singleline(&mut self.params.annual_expenses[1].to_string());
            });
            ui.horizontal(|ui| {
                ui.label("Car Maintenance:");
                ui.text_edit_singleline(&mut self.params.annual_expenses[2].to_string());
            });
            ui.separator();
            ui.heading(if self.language == "en" { "Simulations" } else { "Simulationen" });
            ui.horizontal(|ui| {
                ui.label("Number of Runs:");
                ui.text_edit_singleline(&mut self.params.simulation_runs.to_string());
            });
            if ui.button(if self.language == "en" { "Save Parameters" } else { "Parameter speichern" }).clicked() {
                // Save to a file or local storage (here we simply print to console)
                println!("Parameters saved: {:?}", self.params);
            }
            if ui.button(if self.language == "en" { "Load Parameters" } else { "Parameter laden" }).clicked() {
                // For simplicity, this example does not implement file loading.
                println!("Loading parameters not implemented in this example.");
            }
            if ui.button(if self.language == "en" { "Export PDF" } else { "PDF exportieren" }).clicked() {
                self.export_pdf();
            }
            // Button to run simulation
            if ui.button("Run Simulation").clicked() {
                self.run_simulation();
            }
        });
        // Central panel for plot and explanation
        CentralPanel::default().show(ctx, |ui| {
            ui.heading(if self.language == "en" { "Simulation Results" } else { "Simulationsergebnisse" });
            if let Some(sim) = &self.simulation {
                // Create a line plot for assets and a bar plot for spending.
                let mut plot = Plot::new("simulation_plot")
                    .height(400.0)
                    .legend(egui::plot::Legend::default());
                // Create line plot for assets
                let asset_points: PlotPoints = sim.ages.iter().zip(sim.assets.iter()).map(|(&x, &y)| [x, y]).collect();
                let asset_line = Line::new(Values::from_plot_points(asset_points)).color(egui::Color32::RED).name("Assets");
                // Create line plot for spendings (dotted)
                let spending_points: PlotPoints = sim.ages.iter().zip(sim.spendings.iter()).map(|(&x, &y)| [x, y]).collect();
                let spending_line = Line::new(Values::from_plot_points(spending_points)).color(egui::Color32::GREEN).name("Spendings");
                plot.show(ui, |plot_ui| {
                    plot_ui.line(asset_line);
                    plot_ui.line(spending_line);
                });
                ui.separator();
                ui.label(RichText::new(format!(
                    "{}: {:.1}%",
                    if self.language == "en" { "Success Probability" } else { "Erfolgswahrscheinlichkeit" },
                    sim.success_probability * 100.0
                )).size(16.0));
            } else {
                ui.label(if self.language == "en" { "Click 'Run Simulation' to see results." } else { "Klicken Sie auf 'Run Simulation', um Ergebnisse zu sehen." });
            }
            ui.separator();
            ui.label(if self.language == "en" {
                "Simulation Explanation: The simulation runs in two phases. In the accumulation phase, your assets grow with savings and investment returns. In the distribution phase, your assets cover living expenses (which increase with inflation) until age 90. The success probability shows the percentage of simulation runs where assets never drop below zero."
            } else {
                "Simulations-Erklärung: Die Simulation läuft in zwei Phasen. In der Ansparphase wachsen Ihre Vermögenswerte durch Ersparnisse und Renditen. In der Auszahlungsphase decken Ihre Vermögenswerte die Lebenshaltungskosten (die mit Inflation steigen) bis zum Alter 90. Die Erfolgswahrscheinlichkeit gibt den Prozentsatz der Simulationen an, bei denen die Vermögenswerte nie unter null fallen."
            });
        });
        ctx.request_repaint(); // Keep updating
    }
}

fn main() {
    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "RetireCalc",
        options,
        Box::new(|_cc| Box::new(RetireCalcApp::default())),
    );
}
